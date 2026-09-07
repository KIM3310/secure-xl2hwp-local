from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

from app.core.settings import Settings
from app.services.pipeline_service import PipelineService


def test_pipeline_end_to_end(tmp_path: Path) -> None:
    input_path = tmp_path / "input.xlsx"
    output_dir = tmp_path / "output"

    df = pd.DataFrame(
        [
            {
                "Project ID": "PJT-2026-001",
                "Project Name": "로컬 구축",
                "Owner": "홍길동",
                "Budget": 1000000,
                "Progress": 60,
                "State": "진행중",
                "Report Date": "2026-02-19",
            }
        ]
    )
    df.to_excel(input_path, index=False)

    settings = Settings(enable_llm=False)
    service = PipelineService(settings=settings, spec_base_path=Path("specs"))

    outcome = service.process(
        input_path=input_path,
        output_dir=output_dir,
        contract_name="default",
        profile_name="default",
    )

    assert outcome.metrics["row_count"] == 1
    assert outcome.artifacts.normalized_xlsx.exists()
    assert outcome.artifacts.normalized_csv.exists()
    assert outcome.artifacts.report_json.exists()
    assert outcome.artifacts.hancom_payload_json.exists()
    assert outcome.artifacts.hancom_preview_txt is not None
    assert outcome.artifacts.hancom_preview_txt.exists()


def test_repeated_exports_in_same_second_preserve_previous_artifacts(tmp_path: Path) -> None:
    input_path = tmp_path / "input.xlsx"
    output_dir = tmp_path / "output"
    service = PipelineService(settings=Settings(enable_llm=False), spec_base_path=Path("specs"))
    clock = Mock()
    clock.now.return_value.strftime.return_value = "20260907T000000Z"
    with patch("app.services.export_service.datetime", clock):
        pd.DataFrame(
            [
                {
                    "Project ID": "P-001",
                    "Project Name": "first",
                    "Owner": "demo",
                    "State": "진행중",
                    "Budget": 100,
                }
            ]
        ).to_excel(input_path, index=False)
        first = service.process(input_path, output_dir, "default", "default")
        original = {path: path.read_bytes() for path in vars(first.artifacts).values() if path}
        pd.DataFrame(
            [
                {
                    "Project ID": "P-002",
                    "Project Name": "second",
                    "Owner": "demo",
                    "State": "진행중",
                    "Budget": 200,
                }
            ]
        ).to_excel(input_path, index=False)
        second = service.process(input_path, output_dir, "default", "default")
    first_paths = set(original)
    second_paths = {path for path in vars(second.artifacts).values() if path}
    assert first_paths.isdisjoint(second_paths)
    assert all(path.read_bytes() == content for path, content in original.items())
    assert all(path.exists() for path in second_paths)
