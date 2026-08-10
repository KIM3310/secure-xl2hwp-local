import sys
from pathlib import Path

import pytest

from app.core.settings import Settings
from app.services.auth_service import AuthService
from app.services.speckit_loader import SpecKitLoader
from scripts.hash_password import hash_password as hash_password_for_registry
from scripts.hash_password import main as hash_password_main

TEST_AUTH_PASSWORD_PEPPER = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
TEST_JWT_SECRET_KEY = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def test_authenticate_and_verify_token() -> None:
    settings = Settings(
        auth_enabled=True,
        user_registry_name="users_test",
        auth_password_pepper=TEST_AUTH_PASSWORD_PEPPER,
        jwt_secret_key=TEST_JWT_SECRET_KEY,
    )
    loader = SpecKitLoader(base_path=Path("specs"))
    auth_service = AuthService(settings=settings, spec_loader=loader)

    user = auth_service.authenticate("demo-admin", "admin123!")
    assert user is not None
    assert user.user_id == "demo-admin"
    assert user.role == "Admin"

    fail_user = auth_service.authenticate("demo-admin", "wrong-password")
    assert fail_user is None

    token, _ = auth_service.issue_access_token(user)
    verified = auth_service.verify_token(token)
    assert verified.user_id == "demo-admin"
    assert verified.role == "Admin"


def test_pbkdf2_hash_verification() -> None:
    settings = Settings(
        auth_enabled=True,
        user_registry_name="users_test",
        auth_password_pepper=TEST_AUTH_PASSWORD_PEPPER,
        jwt_secret_key=TEST_JWT_SECRET_KEY,
    )
    loader = SpecKitLoader(base_path=Path("specs"))
    auth_service = AuthService(settings=settings, spec_loader=loader)

    pbkdf2_hash = auth_service.hash_password_pbkdf2(
        password="strong-password",
        salt="abcd1234",
    )

    assert auth_service._verify_password(pbkdf2_hash, "strong-password")
    assert not auth_service._verify_password(pbkdf2_hash, "wrong-password")


def test_registry_hash_script_generates_only_pbkdf2() -> None:
    password_hash = hash_password_for_registry(
        password="strong-password",
        pepper=TEST_AUTH_PASSWORD_PEPPER,
        salt="0123456789abcdef0123456789abcdef",
    )

    scheme, iterations, salt, digest = password_hash.split("$")
    assert scheme == "pbkdf2_sha256"
    assert int(iterations) >= 390_000
    assert salt == "0123456789abcdef0123456789abcdef"
    assert len(digest) == 64


def test_registry_hash_script_rejects_legacy_fast_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "hash_password.py",
            "--password",
            "strong-password",
            "--pepper",
            TEST_AUTH_PASSWORD_PEPPER,
            "--algo",
            "sha256",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        hash_password_main()

    assert exc_info.value.code == 2
