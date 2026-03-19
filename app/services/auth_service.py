from __future__ import annotations

import binascii
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

    def hash_password(self, password: str) -> str:
        material = f"{password}{self.settings.auth_password_pepper}".encode()
        return hashlib.sha256(material).hexdigest()

    def hash_password_pbkdf2(
        self,
        password: str,
        salt: str,
        iterations: int = 390000,
    ) -> str:
        material = f"{password}{self.settings.auth_password_pepper}".encode()
        digest = hashlib.pbkdf2_hmac("sha256", material, salt.encode(), iterations)
        return f"pbkdf2_sha256${iterations}${salt}${binascii.hexlify(digest).decode()}"

    def _verify_password(self, stored_hash: str, password: str) -> bool:
        if stored_hash.startswith("pbkdf2_sha256$"):
            try:
                _, iterations_str, salt, expected_hex = stored_hash.split("$", maxsplit=3)
                iterations = int(iterations_str)
                actual = self.hash_password_pbkdf2(password=password, salt=salt, iterations=iterations)
                actual_hex = actual.split("$", maxsplit=3)[-1]
                return hmac.compare_digest(expected_hex, actual_hex)
            except (ValueError, IndexError):
                return False

        expected_hash = stored_hash
        provided_hash = self.hash_password(password)
        return hmac.compare_digest(expected_hash, provided_hash)

    def _load_users(self) -> dict:
        registry = self.spec_loader.load_user_registry(self.settings.user_registry_name)
        return {user.user_id: user for user in registry.users}

    def _refresh_users(self) -> None:
        try:
            self._users = self._load_users()
        except (OSError, ValueError, KeyError) as exc:
            logger.warning("Failed to refresh user registry, using cached users: %s", exc)
