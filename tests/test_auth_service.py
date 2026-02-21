from pathlib import Path

from app.core.settings import Settings
from app.services.auth_service import AuthService
from app.services.speckit_loader import SpecKitLoader

TEST_AUTH_PASSWORD_PEPPER = "test-auth-pepper-very-long-secret-0123456789"
TEST_JWT_SECRET_KEY = "test-jwt-secret-key-very-long-secret-0123456789abcdef"


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
        iterations=1000,
    )

    assert auth_service._verify_password(pbkdf2_hash, "strong-password")
    assert not auth_service._verify_password(pbkdf2_hash, "wrong-password")
