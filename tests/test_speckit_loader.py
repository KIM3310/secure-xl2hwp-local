from pathlib import Path

from app.services.speckit_loader import SpecKitLoader


def test_load_default_specs() -> None:
    loader = SpecKitLoader(base_path=Path("specs"))
    contract = loader.load_contract("default")
    profile = loader.load_profile("default")

    assert contract.dataset == "local_secure_project_status"
    assert any(field.name == "사업명" for field in contract.fields)
    assert profile.profile_name == "default"
    assert "{{PROJECT_NAME}}" in profile.template_mapping
