from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional, Union

from app.core.settings import Settings
from app.pipeline.cot_engine import CotOrchestrator
from app.services.audit_logger import AuditLogger
from app.services.excel_processor import ExcelProcessor
from app.services.export_service import ExportArtifacts, ExportService
from app.services.llm_service import LocalLLMService
from app.services.speckit_loader import SpecKitLoader


@dataclass
class PipelineOutcome:
    artifacts: ExportArtifacts
    issues: list[str]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artifacts"] = {k: str(v) for k, v in payload["artifacts"].items()}
        return payload


class PipelineService:
    def __init__(
        self,
        settings: Settings,
        spec_base_path: Union[Path, str] = "specs",
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        self.settings = settings
        self.spec_loader = SpecKitLoader(base_path=spec_base_path)
        self.excel_processor = ExcelProcessor()
        self.export_service = ExportService()
        self.audit_logger = audit_logger

        llm_service = LocalLLMService(
            base_url=settings.ollama_base_url,
            primary_model=settings.llm_primary_model,
            fallback_model=settings.llm_fallback_model,
            timeout_seconds=settings.llm_timeout_seconds,
            unavailable_cooldown_seconds=settings.llm_unavailable_cooldown_seconds,
        )
        self.cot_orchestrator = CotOrchestrator(
            llm_service=llm_service,
            enable_llm=settings.enable_llm,
        )

    def process(
        self,
        input_path: Union[Path, str],
        output_dir: Union[Path, str],
        contract_name: str = "default",
        profile_name: str = "default",
        template_name: str = "default",
        template_path: Optional[Union[Path, str]] = None,
        actor: Optional[dict[str, str]] = None,
        request_id: Optional[str] = None,
    ) -> PipelineOutcome:
        self._audit(
            event_type="pipeline.process",
            status="started",
            actor=actor,
            request_id=request_id,
            details={
                "input_path": str(input_path),
                "output_dir": str(output_dir),
                "contract_name": contract_name,
                "profile_name": profile_name,
                "template_name": template_name,
                "template_path": str(template_path) if template_path else None,
            },
        )

        try:
            return self._run_process(
                input_path=input_path,
                output_dir=output_dir,
                contract_name=contract_name,
                profile_name=profile_name,
                template_name=template_name,
                template_path=template_path,
                actor=actor,
                request_id=request_id,
            )
        except (ValueError, OSError, KeyError, TypeError) as exc:
            self._audit(
                event_type="pipeline.process",
                status="failed",
                actor=actor,
                request_id=request_id,
                details={"error": str(exc)},
            )
            raise

    def _run_process(
        self,
        input_path: Union[Path, str],
        output_dir: Union[Path, str],
        contract_name: str,
        profile_name: str,
        template_name: str,
        template_path: Optional[Union[Path, str]],
        actor: Optional[dict[str, str]],
        request_id: Optional[str],
    ) -> PipelineOutcome:
        contract = self.spec_loader.load_contract(contract_name)
        profile = self.spec_loader.load_profile(profile_name)
        template_profile = self.spec_loader.load_template_profile(template_name)

        raw_df = self.excel_processor.load_sheet(input_path, profile.sheet_name)
        processed = self.excel_processor.apply_profile(raw_df, profile)

        contract_issues = self.excel_processor.validate_against_contract(processed.dataframe, contract)
        issues = processed.issues + contract_issues

        cot_result = self.cot_orchestrator.run(processed.dataframe, contract, profile)

        artifacts = self.export_service.export(
            dataframe=processed.dataframe,
            cot_result=cot_result,
            contract=contract,
            profile=profile,
            template_profile=template_profile,
            input_path=input_path,
            output_dir=output_dir,
            processing_issues=issues,
            template_path=template_path,
        )

        metrics = {
            **processed.metrics,
            "issue_count": len(issues),
            "contract": contract_name,
            "profile": profile_name,
            "template": template_name,
            "request_id": request_id,
        }

        outcome = PipelineOutcome(artifacts=artifacts, issues=issues, metrics=metrics)
        self._audit(
            event_type="pipeline.process",
            status="succeeded",
            actor=actor,
            request_id=request_id,
            details={
                "row_count": metrics.get("row_count"),
                "issue_count": metrics.get("issue_count"),
                "artifacts": {k: str(v) for k, v in outcome.to_dict()["artifacts"].items()},
            },
        )
        return outcome

    def _audit(
        self,
        event_type: str,
        status: str,
        actor: Optional[dict[str, str]],
        request_id: Optional[str],
        details: dict[str, Any],
    ) -> None:
        if not self.audit_logger:
            return
        try:
            self.audit_logger.log_event(
                event_type=event_type,
                status=status,
                actor=actor,
                request_id=request_id,
                details=details,
            )
        except OSError:
            # Audit failure must not block business processing.
            return
