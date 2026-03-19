from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

import pandas as pd

from app.services.speckit_models import CleanupProfile, DataContract


@dataclass
class ProcessResult:
    dataframe: pd.DataFrame
    issues: list[str]
    metrics: dict[str, Any]


class ExcelProcessor:
    def load_sheet(self, input_path: Union[Path, str], sheet_name: Union[str, int]) -> pd.DataFrame:
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")
        df = pd.read_excel(path, sheet_name=sheet_name)
        return df

    def apply_profile(self, df: pd.DataFrame, profile: CleanupProfile) -> ProcessResult:
        work = df.copy()
        issues: list[str] = []

        work.columns = [str(col).strip() for col in work.columns]

        if profile.rename_columns:
            work = work.rename(columns=profile.rename_columns)

        if profile.drop_columns:
            existing_drop_columns = [col for col in profile.drop_columns if col in work.columns]
            work = work.drop(columns=existing_drop_columns)

        if profile.required_columns:
            missing_required = [col for col in profile.required_columns if col not in work.columns]
            if missing_required:
                raise ValueError(f"Missing required columns from profile: {missing_required}")

        for replace_rule in profile.regex_replace:
            if replace_rule.column in work.columns:
                work[replace_rule.column] = (
                    work[replace_rule.column]
                    .astype(str)
                    .str.replace(replace_rule.pattern, replace_rule.replacement, regex=True)
                )

        for column, default_value in profile.fill_defaults.items():
            if column in work.columns:
                work[column] = work[column].fillna(default_value)

        for column, cast_type in profile.type_cast.items():
            if column not in work.columns:
                continue
            try:
                work[column] = self._cast_column(work[column], cast_type)
            except (ValueError, TypeError) as exc:  # pragma: no cover - defensive
                issues.append(f"Type cast failed: column={column}, type={cast_type}, error={exc}")

        for derived_rule in profile.derived_columns:
            try:
                work[derived_rule.name] = self._derive_column(work, derived_rule.expression)
            except (ValueError, KeyError, TypeError) as exc:  # pragma: no cover - defensive
                issues.append(
                    f"Derived column failed: column={derived_rule.name}, expr={derived_rule.expression}, error={exc}"
                )

        metrics = {
            "row_count": int(len(work)),
            "column_count": int(len(work.columns)),
            "columns": list(map(str, work.columns)),
        }
        return ProcessResult(dataframe=work, issues=issues, metrics=metrics)

    def validate_against_contract(self, df: pd.DataFrame, contract: DataContract) -> list[str]:
        issues: list[str] = []
        required_fields = [field.name for field in contract.fields if field.required]

        for required in required_fields:
            if required not in df.columns:
                issues.append(f"Required contract field missing: {required}")

        for unique_col in contract.constraints.unique:
            if unique_col in df.columns and df[unique_col].duplicated().any():
                duplicate_count = int(df[unique_col].duplicated().sum())
                issues.append(f"Unique constraint violation: {unique_col} duplicated={duplicate_count}")

        for non_negative_col in contract.constraints.non_negative:
            if non_negative_col in df.columns:
                numeric = pd.to_numeric(df[non_negative_col], errors="coerce")
                negative_count = int((numeric < 0).sum())
                if negative_count > 0:
                    issues.append(
                        f"Non-negative constraint violation: {non_negative_col} negatives={negative_count}"
                    )

        return issues

    @staticmethod
    def _cast_column(series: pd.Series, cast_type: str) -> pd.Series:
        if cast_type == "string":
            return series.astype(str).str.strip()
        if cast_type == "int":
            return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)
        if cast_type == "float":
            return pd.to_numeric(series, errors="coerce").astype(float)
        if cast_type == "bool":
            normalized = series.astype(str).str.lower().str.strip()
            return normalized.isin(["true", "1", "yes", "y", "t"])
        if cast_type == "date":
            return pd.to_datetime(series, errors="coerce")
        raise ValueError(f"Unsupported cast type: {cast_type}")

    @staticmethod
    def _derive_column(df: pd.DataFrame, expression: str) -> pd.Series:
        if expression.startswith("risk_from_progress:"):
            source_col = expression.split(":", maxsplit=1)[1].strip()
            numeric = pd.to_numeric(df[source_col], errors="coerce").fillna(0)
            out = pd.Series(index=df.index, dtype="object")
            out[numeric < 50] = "high"
            out[(numeric >= 50) & (numeric < 80)] = "medium"
            out[numeric >= 80] = "low"
            return out

        if expression.startswith("concat:"):
            cols = [part.strip() for part in expression.split(":", maxsplit=1)[1].split(",")]
            return df[cols].astype(str).agg(" ".join, axis=1).str.strip()

        raise ValueError(f"Unsupported derived expression: {expression}")
