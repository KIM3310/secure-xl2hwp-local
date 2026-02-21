import pytest

from app.core.settings import Settings


def test_settings_reject_short_jwt_secret_when_auth_enabled() -> None:
    with pytest.raises(ValueError):
        Settings(auth_enabled=True, jwt_secret_key="short")


def test_settings_allow_short_jwt_secret_when_auth_disabled() -> None:
    settings = Settings(auth_enabled=False, jwt_secret_key="short")
    assert settings.auth_enabled is False


def test_settings_reject_short_export_signing_key_when_enabled() -> None:
    with pytest.raises(ValueError):
        Settings(export_signing_enabled=True, export_signing_key="short")


def test_settings_allow_short_export_signing_key_when_disabled() -> None:
    settings = Settings(export_signing_enabled=False, export_signing_key="short")
    assert settings.export_signing_enabled is False


def test_settings_reject_negative_llm_cooldown() -> None:
    with pytest.raises(ValueError):
        Settings(llm_unavailable_cooldown_seconds=-1)


def test_settings_reject_invalid_auth_login_guard_values() -> None:
    with pytest.raises(ValueError):
        Settings(auth_login_max_failures=0)
    with pytest.raises(ValueError):
        Settings(auth_login_window_seconds=5)
    with pytest.raises(ValueError):
        Settings(auth_login_lock_seconds=0)


def test_settings_reject_placeholder_secrets_when_enabled() -> None:
    with pytest.raises(ValueError):
        Settings(auth_enabled=True, jwt_secret_key="change-this-jwt-secret-minimum-32-characters")
    with pytest.raises(ValueError):
        Settings(auth_enabled=True, auth_password_pepper="change-this-pepper")
    with pytest.raises(ValueError):
        Settings(export_signing_enabled=True, export_signing_key="change-this-export-signing-key-minimum-32-characters")


def test_settings_reject_blank_allowed_base_dirs() -> None:
    with pytest.raises(ValueError):
        Settings(allowed_input_base_dir=" ")
    with pytest.raises(ValueError):
        Settings(allowed_output_base_dir="")
    with pytest.raises(ValueError):
        Settings(allowed_template_base_dir="   ")
