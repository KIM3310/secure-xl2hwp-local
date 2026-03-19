from pathlib import Path

import pandas as pd

from app.pipeline.cot_engine import CotResult
from app.services.speckit_loader import SpecKitLoader
from app.services.template_engine import HancomTemplateEngine


def test_template_engine_detect_and_map_placeholders() -> None:
    loader = SpecKitLoader(base_path=Path("specs"))
    contract = loader.load_contract("default")
    profile = loader.load_profile("default")
    template_profile = loader.load_template_profile("default")

    df = pd.DataFrame(
        [
            {
                "관리번호": "PJT-1",
                "사업명": "테스트 사업",
                "담당자": "홍길동",
                "사업비": 150000000,
                "진행률": 67.2,
                "상태": "진행중",
                "보고일자": "2026-02-19",
                "위험등급": "medium",
            }
        ]
    )

    cot_result = CotResult(
        stage_outputs={
            "document_mapping": {
                "payload": {
                    "{{AI_SUMMARY}}": "요약",
                    "{{AI_RISK_NOTE}}": "리스크",
                }
            }
        },
        trace=[],
    )

    engine = HancomTemplateEngine()
    result = engine.build_payload(
        dataframe=df,
        cot_result=cot_result,
        profile=profile,
        contract=contract,
        template_profile=template_profile,
        template_path=Path("examples/input/sample_report_template.txt"),
    )

    placeholders = result["template_placeholders"]
    assert placeholders["{{BUDGET}}"] == "150,000,000원"
    assert placeholders["{{PROGRESS}}"] == "67.2%"
    assert "{{PROJECT_TABLE_ROWS}}" in placeholders
    assert "{{AI_SUMMARY}}" in result["unmapped_placeholders"]
    assert "{{AI_SUMMARY}}" in placeholders


def test_template_engine_safe_value_handles_collection() -> None:
    engine = HancomTemplateEngine()

    safe_dict = engine._safe_value({"a": 1, "b": [1, 2]})
    safe_list = engine._safe_value(["x", "y"])

    assert isinstance(safe_dict, str)
    assert safe_dict.startswith("{")
    assert isinstance(safe_list, str)
    assert safe_list.startswith("[")


def test_template_engine_detects_template_drift_inputs() -> None:
    loader = SpecKitLoader(base_path=Path("specs"))
    template_profile = loader.load_template_profile("default")
    engine = HancomTemplateEngine()

    detected = engine.detect_placeholders(Path("examples/input/sample_report_template.txt"))
    configured = set(template_profile.placeholder_rules.keys())
    missing_rules = sorted(set(detected) - configured)

    assert "{{PROJECT_ID}}" in detected
    assert "{{PROJECT_TABLE_ROWS}}" in detected
    assert "{{PROJECT_TABLE_ROWS}}" not in configured
    assert "{{PROJECT_TABLE_ROWS}}" in missing_rules
