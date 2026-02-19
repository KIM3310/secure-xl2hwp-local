from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd

from app.services.llm_service import LocalLLMService
from app.services.speckit_models import CleanupProfile, DataContract


@dataclass
class CotResult:
    stage_outputs: dict[str, Any]
    trace: list[str]


class CotOrchestrator:
    """Three-stage CoT-like orchestrator with deterministic fallback.

    Stage 1: infer schema semantics
    Stage 2: suggest cleanup actions
    Stage 3: build document mapping payload
    """

    def __init__(self, llm_service: Optional[LocalLLMService], enable_llm: bool) -> None:
        self.llm_service = llm_service
        self.enable_llm = enable_llm and llm_service is not None

    def run(self, df: pd.DataFrame, contract: DataContract, profile: CleanupProfile) -> CotResult:
        trace: list[str] = []

        schema_inference = self._stage_schema_inference(df, contract)
        trace.append("stage1:schema_inference completed")

        cleanup_advice = self._stage_cleanup_advice(df, profile)
        trace.append("stage2:cleanup_advice completed")

        doc_mapping = self._stage_document_mapping(df, profile)
        trace.append("stage3:document_mapping completed")

        return CotResult(
            stage_outputs={
                "schema_inference": schema_inference,
                "cleanup_advice": cleanup_advice,
                "document_mapping": doc_mapping,
            },
            trace=trace,
        )

    def _stage_schema_inference(self, df: pd.DataFrame, contract: DataContract) -> dict[str, Any]:
        deterministic_map = {}
        normalized_columns = {self._normalize(col): col for col in df.columns}

        for field in contract.fields:
            normalized_target = self._normalize(field.name)
            deterministic_map[field.name] = normalized_columns.get(normalized_target)

        if not self.enable_llm:
            return {"mode": "deterministic", "field_map": deterministic_map}

        assert self.llm_service is not None
        prompt = {
            "contract_fields": [field.name for field in contract.fields],
            "columns": [str(col) for col in df.columns],
            "instruction": "Return JSON with field_map object mapping contract_fields -> columns or null",
        }
        response = self.llm_service.chat_json(
            system_prompt="You are a strict data schema mapper. Return valid JSON only.",
            user_prompt=str(prompt),
        )
        if not response:
            return {"mode": "deterministic", "field_map": deterministic_map, "llm_used": False}

        field_map = response.get("field_map", deterministic_map)
        return {"mode": "llm+deterministic", "field_map": field_map, "llm_used": True}

    def _stage_cleanup_advice(self, df: pd.DataFrame, profile: CleanupProfile) -> dict[str, Any]:
        missing_ratio = {
            col: float(df[col].isna().mean()) for col in df.columns if float(df[col].isna().mean()) > 0
        }
        deterministic_advice = {
            "high_missing_columns": [
                col for col, ratio in missing_ratio.items() if ratio >= 0.4
            ],
            "suggest_drop_duplicates": True,
            "profile_required_columns": profile.required_columns,
        }

        if not self.enable_llm:
            return {"mode": "deterministic", "advice": deterministic_advice}

        assert self.llm_service is not None
        prompt = {
            "missing_ratio": missing_ratio,
            "required_columns": profile.required_columns,
            "instruction": "Return JSON {advice:{...}} with concise cleanup actions",
        }
        response = self.llm_service.chat_json(
            system_prompt="You are a strict data quality assistant. Return valid JSON only.",
            user_prompt=str(prompt),
        )
        if not response:
            return {"mode": "deterministic", "advice": deterministic_advice, "llm_used": False}

        merged_advice = response.get("advice", {})
        merged_advice.setdefault("high_missing_columns", deterministic_advice["high_missing_columns"])
        merged_advice.setdefault("suggest_drop_duplicates", True)
        return {"mode": "llm+deterministic", "advice": merged_advice, "llm_used": True}

    def _stage_document_mapping(self, df: pd.DataFrame, profile: CleanupProfile) -> dict[str, Any]:
        if df.empty:
            first_row = {}
        else:
            first_row = {str(k): self._safe_json(v) for k, v in df.iloc[0].to_dict().items()}

        mapped_payload = {}
        for placeholder, source_column in profile.template_mapping.items():
            mapped_payload[placeholder] = first_row.get(source_column)

        mapped_payload["{{ROW_COUNT}}"] = len(df)

        if not self.enable_llm:
            return {"mode": "deterministic", "payload": mapped_payload}

        assert self.llm_service is not None
        prompt = {
            "first_row": first_row,
            "row_count": len(df),
            "instruction": "Return JSON {summary:'...', risk_note:'...'} in Korean",
        }
        response = self.llm_service.chat_json(
            system_prompt="You create short operational summary for an internal Korean business report.",
            user_prompt=str(prompt),
        )
        if not response:
            return {
                "mode": "deterministic",
                "payload": mapped_payload,
                "narrative": "LLM unavailable, deterministic payload only.",
            }

        mapped_payload["{{AI_SUMMARY}}"] = response.get("summary", "")
        mapped_payload["{{AI_RISK_NOTE}}"] = response.get("risk_note", "")
        return {"mode": "llm+deterministic", "payload": mapped_payload, "narrative": response}

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(str(value).strip().lower().split())

    @staticmethod
    def _safe_json(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
