from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Union

import pandas as pd

from app.pipeline.cot_engine import CotResult
from app.services.speckit_models import CleanupProfile, DataContract, HancomTemplateProfile

PLACEHOLDER_PATTERN = re.compile(r"\{\{[A-Z0-9_]+\}\}")


class HancomTemplateEngine:
    def build_payload(
        self,
        dataframe: pd.DataFrame,
        cot_result: CotResult,
        profile: CleanupProfile,
        contract: DataContract,
        template_profile: HancomTemplateProfile,
        template_path: Union[Path, str, None] = None,
    ) -> dict[str, Any]:
        first_row = dataframe.iloc[0].to_dict() if not dataframe.empty else {}
        metrics = {
            "row_count": int(len(dataframe)),
            "column_count": int(len(dataframe.columns)),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "columns": [str(col) for col in dataframe.columns],
        }

        cot_document_mapping = cot_result.stage_outputs.get("document_mapping", {})
        cot_payload = cot_document_mapping.get("payload", {})

        payload: dict[str, Any] = {}

        # Keep backward compatibility with old template_mapping behavior.
        for placeholder, source_column in profile.template_mapping.items():
            payload[placeholder] = self._safe_value(first_row.get(source_column))

        payload["{{ROW_COUNT}}"] = metrics["row_count"]
        payload["{{COLUMN_COUNT}}"] = metrics["column_count"]

        for placeholder, rule in template_profile.placeholder_rules.items():
            value = self._resolve_source(
                source=rule.source,
                first_row=first_row,
                metrics=metrics,
                cot_payload=cot_payload,
                contract=contract,
                profile=profile,
            )
            if value is None:
                value = rule.default
            payload[placeholder] = self._transform(value, rule.transform)

        for section in template_profile.table_sections:
            table_text = self._render_table_section(dataframe, section.columns, section.row_template, section.max_rows)
            payload[section.placeholder] = table_text if table_text else section.empty_text

        detected_placeholders = self.detect_placeholders(template_path)
        unmapped_placeholders = sorted(set(detected_placeholders) - set(payload.keys()))

        if template_profile.include_unmapped_placeholders:
            for placeholder in unmapped_placeholders:
                payload[placeholder] = ""

        return {
            "template_name": template_profile.template_name,
            "template_path": str(template_path) if template_path else None,
            "detected_placeholders": detected_placeholders,
            "unmapped_placeholders": unmapped_placeholders,
            "template_placeholders": {k: self._safe_value(v) for k, v in payload.items()},
        }

    def detect_placeholders(self, template_path: Union[Path, str, None]) -> list[str]:
        if not template_path:
            return []

        path = Path(template_path)
        if not path.exists():
            return []

        matched: set[str] = set()

        try:
            if path.suffix.lower() == ".hwpx" and zipfile.is_zipfile(path):
                with zipfile.ZipFile(path, "r") as zf:
                    for entry in zf.infolist():
                        if not entry.filename.lower().endswith((".xml", ".txt", ".html")):
                            continue
                        text = zf.read(entry.filename).decode("utf-8", errors="ignore")
                        matched.update(PLACEHOLDER_PATTERN.findall(text))
            else:
                text = path.read_text(encoding="utf-8", errors="ignore")
                matched.update(PLACEHOLDER_PATTERN.findall(text))
        except Exception:
            return []

        return sorted(matched)

    def _resolve_source(
        self,
        source: str,
        first_row: dict[str, Any],
        metrics: dict[str, Any],
        cot_payload: dict[str, Any],
        contract: DataContract,
        profile: CleanupProfile,
    ) -> Any:
        if source.startswith("literal:"):
            return source.split(":", maxsplit=1)[1]

        if source.startswith("first_row."):
            key = source.split(".", maxsplit=1)[1]
            return first_row.get(key)

        if source.startswith("metrics."):
            key = source.split(".", maxsplit=1)[1]
            return metrics.get(key)

        if source.startswith("cot_payload."):
            key = source.split(".", maxsplit=1)[1]
            return cot_payload.get(key)

        if source.startswith("contract."):
            key = source.split(".", maxsplit=1)[1]
            return contract.model_dump().get(key)

        if source.startswith("profile."):
            key = source.split(".", maxsplit=1)[1]
            return profile.model_dump().get(key)

        return first_row.get(source)

    def _transform(self, value: Any, transform: str) -> Any:
        if value is None:
            return None

        if transform == "identity":
            return value

        if transform == "currency_krw":
            numeric = pd.to_numeric([value], errors="coerce")[0]
            if pd.isna(numeric):
                return str(value)
            return f"{int(numeric):,}원"

        if transform == "percent":
            numeric = pd.to_numeric([value], errors="coerce")[0]
            if pd.isna(numeric):
                return str(value)
            return f"{float(numeric):.1f}%"

        if transform == "upper":
            return str(value).upper()

        if transform == "lower":
            return str(value).lower()

        if transform == "json":
            return json.dumps(value, ensure_ascii=False)

        if transform.startswith("date:"):
            fmt = transform.split(":", maxsplit=1)[1]
            parsed = pd.to_datetime(value, errors="coerce")
            if pd.isna(parsed):
                return str(value)
            return parsed.strftime(fmt)

        return value

    def _render_table_section(
        self,
        dataframe: pd.DataFrame,
        columns: list[str],
        row_template: str,
        max_rows: int,
    ) -> str:
        if dataframe.empty:
            return ""

        lines: list[str] = []
        sample = dataframe.head(max_rows)

        for _, row in sample.iterrows():
            row_context = {col: self._safe_value(row.get(col)) for col in columns}
            safe_context = {k: "" if v is None else str(v) for k, v in row_context.items()}

            try:
                rendered = row_template.format(**safe_context)
            except KeyError:
                rendered = " | ".join(safe_context.get(col, "") for col in columns)
            lines.append(rendered)

        if len(dataframe) > max_rows:
            lines.append(f"... 외 {len(dataframe) - max_rows}건")

        return "\n".join(lines)

    @staticmethod
    def _safe_value(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (list, tuple, dict, set)):
            return json.dumps(value, ensure_ascii=False, default=str)
        try:
            missing = pd.isna(value)
            if isinstance(missing, bool) and missing:
                return None
        except Exception:
            pass
        return str(value)
