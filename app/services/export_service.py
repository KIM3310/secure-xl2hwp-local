from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd

from app.pipeline.cot_engine import CotResult
from app.services.speckit_models import CleanupProfile, DataContract, HancomTemplateProfile
from app.services.template_engine import HancomTemplateEngine


@dataclass
class ExportArtifacts:
    normalized_xlsx: Path
    normalized_csv: Path
    report_json: Path
    hancom_payload_json: Path
    hancom_preview_txt: Optional[Path] = None


class ExportService:
    def __init__(self) -> None:
        self.template_engine = HancomTemplateEngine()

    def export(
        self,
        dataframe: pd.DataFrame,
        cot_result: CotResult,
        contract: DataContract,
        profile: CleanupProfile,
        template_profile: HancomTemplateProfile,
        input_path: Union[Path, str],
        output_dir: Union[Path, str],
        processing_issues: list[str],
        template_path: Union[Path, str, None] = None,
    ) -> ExportArtifacts:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        stem = Path(input_path).stem
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        normalized_xlsx = out_dir / f"{stem}.normalized.{timestamp}.xlsx"
        normalized_csv = out_dir / f"{stem}.normalized.{timestamp}.csv"
        report_json = out_dir / f"{stem}.report.{timestamp}.json"
        hancom_payload_json = out_dir / f"{stem}.hancom_payload.{timestamp}.json"
        hancom_preview_txt = out_dir / f"{stem}.hancom_preview.{timestamp}.txt"

        dataframe.to_excel(normalized_xlsx, index=False)
        dataframe.to_csv(normalized_csv, index=False, encoding="utf-8-sig")

        template_payload = self.template_engine.build_payload(
            dataframe=dataframe,
            cot_result=cot_result,
            profile=profile,
            contract=contract,
            template_profile=template_profile,
            template_path=template_path,
        )
        payload = template_payload.get("template_placeholders", {})

        report_payload: dict[str, Any] = {
            "generated_at_utc": timestamp,
            "input_file": str(input_path),
            "template_path": str(template_path) if template_path else None,
            "contract": contract.model_dump(),
            "profile": profile.model_dump(),
            "template_profile": template_profile.model_dump(),
            "processing_issues": processing_issues,
            "cot_trace": cot_result.trace,
            "cot_outputs": cot_result.stage_outputs,
            "template_mapping": template_payload,
            "row_count": len(dataframe),
            "column_count": len(dataframe.columns),
        }

        hancom_payload = {
            "generated_at_utc": timestamp,
            "source_file": str(input_path),
            "template_name": template_profile.template_name,
            "template_path": str(template_path) if template_path else None,
            "dataset": contract.dataset,
            "template_placeholders": payload,
            "detected_placeholders": template_payload.get("detected_placeholders", []),
            "unmapped_placeholders": template_payload.get("unmapped_placeholders", []),
            "notes": [
                "Use this payload with a Hancom template connector.",
                "Template placeholders should match keys like {{PROJECT_NAME}}.",
            ],
        }

        self._write_json(report_json, report_payload)
        self._write_json(hancom_payload_json, hancom_payload)
        self._write_preview(hancom_preview_txt, payload)

        return ExportArtifacts(
            normalized_xlsx=normalized_xlsx,
            normalized_csv=normalized_csv,
            report_json=report_json,
            hancom_payload_json=hancom_payload_json,
            hancom_preview_txt=hancom_preview_txt,
        )

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)

    @staticmethod
    def _write_preview(path: Path, placeholders: dict[str, Any]) -> None:
        lines = [f"{key} = {value}" for key, value in sorted(placeholders.items(), key=lambda item: item[0])]
        with path.open("w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
