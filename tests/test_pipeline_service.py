from pathlib import Path

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
