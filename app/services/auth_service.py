from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from app.core.settings import Settings
from app.services.speckit_loader import SpecKitLoader

logger = logging.getLogger(__name__)

PBKDF2_SCHEME = "pbkdf2_sha256"
PBKDF2_MIN_ITERATIONS = 390_000
PBKDF2_DEFAULT_ITERATIONS = PBKDF2_MIN_ITERATIONS
PBKDF2_MAX_ITERATIONS = 2_000_000
PBKDF2_DIGEST_HEX_LENGTH = 64


@dataclass
class AuthUser:
    user_id: str
    role: str

    def to_dict(self) -> dict[str, str]:
        return {"user_id": self.user_id, "role": self.role}


class AuthService:
    def __init__(self, settings: Settings, spec_loader: SpecKitLoader) -> None:
        self.settings = settings
        self.spec_loader = spec_loader
        self._users = self._load_users()

    def authenticate(self, user_id: str, password: str) -> Optional[AuthUser]:
        self._refresh_users()
        user = self._users.get(user_id)
        if not user or not user.active:
            return None

        if not self._verify_password(user.password_hash, password):
            return None

        return AuthUser(user_id=user.user_id, role=user.role)

    def issue_access_token(self, user: AuthUser) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.settings.jwt_exp_minutes)

        payload = {
            "sub": user.user_id,
            "role": user.role,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": str(uuid.uuid4()),
        }

        token = jwt.encode(payload, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)
        return token, expires_at.isoformat()

    def verify_token(self, token: str) -> AuthUser:
        self._refresh_users()
        decoded = jwt.decode(
            token,
            self.settings.jwt_secret_key,
            algorithms=[self.settings.jwt_algorithm],
        )
        user_id = str(decoded.get("sub", "")).strip()
        role = str(decoded.get("role", "")).strip()
        if not user_id or not role:
            raise jwt.InvalidTokenError("Missing token claims")

        user = self._users.get(user_id)
        if not user or not user.active:
            raise jwt.InvalidTokenError("User is inactive or missing")
        if user.role != role:
            raise jwt.InvalidTokenError("Token role does not match current user role")
        return AuthUser(user_id=user_id, role=role)

    def hash_password_pbkdf2(
        self,
        password: str,
        salt: str,
        iterations: int = PBKDF2_DEFAULT_ITERATIONS,
    ) -> str:
        if not PBKDF2_MIN_ITERATIONS <= iterations <= PBKDF2_MAX_ITERATIONS:
            raise ValueError(
                f"PBKDF2 iterations must be between "
                f"{PBKDF2_MIN_ITERATIONS} and {PBKDF2_MAX_ITERATIONS}"
            )
        if not salt or "$" in salt:
            raise ValueError("PBKDF2 salt must be non-empty and must not contain '$'")

        material = f"{password}{self.settings.auth_password_pepper}".encode()
        digest = hashlib.pbkdf2_hmac("sha256", material, salt.encode(), iterations)
        return f"{PBKDF2_SCHEME}${iterations}${salt}${digest.hex()}"

    def _verify_password(self, stored_hash: str, password: str) -> bool:
        if not stored_hash.startswith(f"{PBKDF2_SCHEME}$"):
            return False

        try:
            scheme, iterations_str, salt, expected_hex = stored_hash.split("$", maxsplit=3)
            if scheme != PBKDF2_SCHEME or len(expected_hex) != PBKDF2_DIGEST_HEX_LENGTH:
                return False
            expected_digest = bytes.fromhex(expected_hex)
            iterations = int(iterations_str)
            actual = self.hash_password_pbkdf2(
                password=password,
                salt=salt,
                iterations=iterations,
            )
            actual_digest = bytes.fromhex(actual.rsplit("$", maxsplit=1)[-1])
            return hmac.compare_digest(expected_digest, actual_digest)
        except (ValueError, IndexError):
            return False

    def _load_users(self) -> dict:
        registry = self.spec_loader.load_user_registry(self.settings.user_registry_name)
        return {user.user_id: user for user in registry.users}

    def _refresh_users(self) -> None:
        try:
            self._users = self._load_users()
        except (OSError, ValueError, KeyError) as exc:
            logger.warning("Failed to refresh user registry, using cached users: %s", exc)
