from pathlib import Path
from typing import Union

import yaml

from app.services.speckit_models import (
    CleanupProfile,
    DataContract,
    HancomTemplateProfile,
    UserRegistry,
)


class SpecKitLoader:
    def __init__(self, base_path: Union[Path, str] = "specs") -> None:
        self.base_path = Path(base_path)

    def load_contract(self, contract_name: str = "default") -> DataContract:
        contract_path = self.base_path / "contracts" / f"{contract_name}.yaml"
        data = self._load_yaml(contract_path)
        return DataContract.model_validate(data)

    def load_profile(self, profile_name: str = "default") -> CleanupProfile:
        profile_path = self.base_path / "profiles" / f"{profile_name}.yaml"
        data = self._load_yaml(profile_path)
        return CleanupProfile.model_validate(data)

    def load_template_profile(self, template_name: str = "default") -> HancomTemplateProfile:
        template_path = self.base_path / "templates" / f"{template_name}.yaml"
        data = self._load_yaml(template_path)
        return HancomTemplateProfile.model_validate(data)

    def load_user_registry(self, registry_name: str = "users") -> UserRegistry:
        registry_path = self.base_path / "security" / f"{registry_name}.yaml"
        data = self._load_yaml(registry_path)
        return UserRegistry.model_validate(data)

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        if not path.exists():
            raise FileNotFoundError(f"Spec file not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        if not isinstance(payload, dict):
            raise ValueError(f"Spec file must contain object at top level: {path}")
        return payload
