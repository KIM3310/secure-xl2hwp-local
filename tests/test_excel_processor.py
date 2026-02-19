import pandas as pd

from app.services.excel_processor import ExcelProcessor
from app.services.speckit_loader import SpecKitLoader


def test_apply_profile_and_contract_validation() -> None:
    loader = SpecKitLoader(base_path="specs")
    profile = loader.load_profile("default")
    contract = loader.load_contract("default")

    source = pd.DataFrame(
        [
            {
                "Project ID": "PJT-001",
                "Project Name": "  테스트   프로젝트  ",
                "Owner": "홍길동",
                "Budget": 100,
                "Progress": 30,
                "State": "진행중",
                "Report Date": "2026-02-19",
            },
            {
                "Project ID": "PJT-001",
                "Project Name": "두번째",
                "Owner": "김영희",
                "Budget": 200,
                "Progress": 90,
                "State": "완료",
                "Report Date": "2026-02-19",
            },
        ]
    )

    processor = ExcelProcessor()
    result = processor.apply_profile(source, profile)
    issues = processor.validate_against_contract(result.dataframe, contract)

    assert "위험등급" in result.dataframe.columns
    assert result.dataframe.loc[0, "사업명"] == "테스트 프로젝트"
    assert any("Unique constraint violation" in msg for msg in issues)
