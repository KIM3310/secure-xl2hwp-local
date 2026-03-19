import json
from pathlib import Path

import pandas as pd

from app.core.settings import Settings
from app.services.audit_logger import AuditLogger
from app.services.pipeline_service import PipelineService


def test_pipeline_writes_audit_events(tmp_path: Path) -> None:
    input_path = tmp_path / "input.xlsx"
    output_dir = tmp_path / "output"
    audit_dir = tmp_path / "audit"

    df = pd.DataFrame(
        [
            {
                "Project ID": "PJT-2026-001",
                "Project Name": "감사로그 테스트",
                "Owner": "홍길동",
                "Budget": 1000000,
                "Progress": 61,
                "State": "진행중",
                "Report Date": "2026-02-19",
            }
        ]
    )
    df.to_excel(input_path, index=False)

    settings = Settings(enable_llm=False, audit_log_dir=str(audit_dir))
    audit_logger = AuditLogger(audit_log_dir=str(audit_dir))
    service = PipelineService(settings=settings, spec_base_path=Path("specs"), audit_logger=audit_logger)

    outcome = service.process(
        input_path=input_path,
        output_dir=output_dir,
        contract_name="default",
        profile_name="default",
        template_name="default",
        template_path="examples/input/sample_report_template.txt",
        actor={"user_id": "tester", "role": "QA"},
        request_id="req-test-1",
    )

    assert outcome.metrics["row_count"] == 1

    log_files = list(audit_dir.glob("*.jsonl"))
    assert len(log_files) == 1

    events = [json.loads(line) for line in log_files[0].read_text(encoding="utf-8").splitlines()]
    statuses = [event["status"] for event in events if event["event_type"] == "pipeline.process"]
    assert "started" in statuses
    assert "succeeded" in statuses
    assert events[0]["prev_hash"] == "GENESIS"
    assert len(events[0]["event_hash"]) == 64
    if len(events) > 1:
        assert events[1]["prev_hash"] == events[0]["event_hash"]
        assert len(events[1]["event_hash"]) == 64
