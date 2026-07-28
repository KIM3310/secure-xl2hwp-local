import pytest

from app.core.settings import Settings

PROTECTED_RUNTIME = {
    "app_env": "prod",
    "runtime_owner": "customer",
    "runtime_workers": 1,
    "auth_rate_limit_mode": "upstream-enforced",
    "audit_storage_mode": "persistent-filesystem",
    "jwt_secret_key": "j" * 48,
    "auth_password_pepper": "p" * 48,
    "export_signing_key": "s" * 48,
}


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


def test_development_defaults_use_ephemeral_secrets_only() -> None:
    settings = Settings(
        app_env="dev",
        jwt_secret_key="",
        auth_password_pepper="",
        export_signing_key="",
    )

    posture = settings.secret_posture()
    assert posture["mode"] == "ephemeral-dev-only"
    assert set(posture["ephemeral_fields"]) == {
        "AUTH_PASSWORD_PEPPER",
        "EXPORT_SIGNING_KEY",
        "JWT_SECRET_KEY",
    }


@pytest.mark.parametrize(
    ("field", "value", "expected_message"),
    [
        ("runtime_owner", "developer", "RUNTIME_OWNER=customer"),
        ("runtime_workers", 2, "RUNTIME_WORKERS=1"),
        ("auth_rate_limit_mode", "process-local", "AUTH_RATE_LIMIT_MODE=upstream-enforced"),
        ("audit_storage_mode", "ephemeral", "AUDIT_STORAGE_MODE=persistent-filesystem"),
        ("jwt_secret_key", "", "JWT_SECRET_KEY must be explicitly configured"),
        ("auth_password_pepper", "", "AUTH_PASSWORD_PEPPER must be explicitly configured"),
        ("export_signing_key", "", "EXPORT_SIGNING_KEY must be explicitly configured"),
    ],
)
def test_protected_runtime_rejects_unmet_customer_boundary(
    field: str,
    value: object,
    expected_message: str,
) -> None:
    values = {**PROTECTED_RUNTIME, field: value}
    with pytest.raises(ValueError, match=expected_message):
        Settings(**values)


def test_protected_runtime_accepts_single_worker_customer_owned_pilot() -> None:
    settings = Settings(**PROTECTED_RUNTIME)

    assert settings.secret_posture()["mode"] == "operator-supplied"
    assert settings.runtime_boundary()["delivery_mode"] == "customer-owned-pilot"
    assert settings.runtime_boundary()["production_ready"] is False
