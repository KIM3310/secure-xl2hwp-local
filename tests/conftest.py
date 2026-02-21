from __future__ import annotations

import pytest

from app.main import auth_service, login_attempt_guard, settings

TEST_AUTH_PASSWORD_PEPPER = "test-auth-pepper-very-long-secret-0123456789"
TEST_JWT_SECRET_KEY = "test-jwt-secret-key-very-long-secret-0123456789abcdef"
TEST_EXPORT_SIGNING_KEY = "test-export-signing-key-very-long-secret-0123456789abcdef"


@pytest.fixture(autouse=True)
def runtime_security_overrides():
    keys = [
        "jwt_secret_key",
        "auth_password_pepper",
        "export_signing_key",
        "user_registry_name",
        "allowed_input_base_dir",
        "allowed_output_base_dir",
        "allowed_template_base_dir",
        "auth_login_max_failures",
        "auth_login_window_seconds",
        "auth_login_lock_seconds",
    ]
    original = {key: getattr(settings, key) for key in keys}

    settings.jwt_secret_key = TEST_JWT_SECRET_KEY
    settings.auth_password_pepper = TEST_AUTH_PASSWORD_PEPPER
    settings.export_signing_key = TEST_EXPORT_SIGNING_KEY
    settings.user_registry_name = "users_test"
    settings.allowed_input_base_dir = "examples/input"
    settings.allowed_output_base_dir = "examples/output"
    settings.allowed_template_base_dir = "examples/input"

    auth_service._users = auth_service._load_users()
    login_attempt_guard.configure(
        max_failures=settings.auth_login_max_failures,
        window_seconds=settings.auth_login_window_seconds,
        lock_seconds=settings.auth_login_lock_seconds,
    )
    login_attempt_guard.reset()

    yield

    for key, value in original.items():
        setattr(settings, key, value)

    try:
        auth_service._users = auth_service._load_users()
    except Exception:
        # Best-effort restore; tests should not fail in teardown.
        pass

    login_attempt_guard.configure(
        max_failures=settings.auth_login_max_failures,
        window_seconds=settings.auth_login_window_seconds,
        lock_seconds=settings.auth_login_lock_seconds,
    )
    login_attempt_guard.reset()
