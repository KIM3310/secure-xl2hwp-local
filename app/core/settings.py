import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field, PrivateAttr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROTECTED_ENVIRONMENTS = {"pilot", "prod", "production", "staging"}


def _generated_secret(length: int = 48) -> str:
    # Avoid shipping a fixed shared secret in source defaults.
    return secrets.token_urlsafe(length)


def _looks_placeholder_secret(value: str) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return True
    return any(marker in text for marker in ("change-this", "replace-me", "__replace__", "your-"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    _ephemeral_secret_fields: set[str] = PrivateAttr(default_factory=set)

    app_name: str = "secure-xl2hwp-local"
    app_env: str = "dev"
    log_level: str = "INFO"
    runtime_owner: Literal["developer", "customer"] = "developer"
    runtime_workers: int = Field(default=1, ge=1)
    auth_rate_limit_mode: Literal["process-local", "upstream-enforced"] = "process-local"
    audit_storage_mode: Literal["ephemeral", "persistent-filesystem"] = "ephemeral"

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    llm_primary_model: str = "qwen2.5:7b"
    llm_fallback_model: str = "qwen2.5:14b"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "qwen/qwen3-next-80b-a3b-thinking"
    openrouter_fallback_model: str = "openai/gpt-5.4-mini"
    openrouter_http_referer: str = "https://secure-xl2hwp-local.pages.dev"
    openrouter_app_title: str = "secure-xl2hwp-local"
    llm_timeout_seconds: int = Field(default=45, ge=1)
    llm_unavailable_cooldown_seconds: int = Field(default=20, ge=0)
    enable_llm: bool = True

    auth_enabled: bool = True
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = Field(default=120, ge=1)
    auth_password_pepper: str = ""
    user_registry_name: str = "users"
    auth_login_max_failures: int = Field(default=5, ge=1)
    auth_login_window_seconds: int = Field(default=300, ge=10)
    auth_login_lock_seconds: int = Field(default=120, ge=1)
    process_allowed_roles: str = "Admin,Analyst"
    max_upload_mb: int = Field(default=50, ge=1)
    allowed_input_base_dir: str = "examples/input"
    allowed_output_base_dir: str = "examples/output"
    allowed_template_base_dir: str = "examples/input"

    audit_log_dir: str = "logs/audit"
    export_signing_enabled: bool = True
    export_signing_key_id: str = "local-hmac-v1"
    export_signing_key: str = ""

    @model_validator(mode="after")
    def validate_security(self) -> "Settings":
        protected_runtime = self.app_env.strip().lower() in PROTECTED_ENVIRONMENTS

        required_secrets = (
            ("jwt_secret_key", "JWT_SECRET_KEY", self.auth_enabled, 48),
            ("auth_password_pepper", "AUTH_PASSWORD_PEPPER", self.auth_enabled, 32),
            ("export_signing_key", "EXPORT_SIGNING_KEY", self.export_signing_enabled, 48),
        )
        for field_name, env_name, enabled, generated_length in required_secrets:
            if not enabled:
                continue
            value = str(getattr(self, field_name) or "").strip()
            if not value:
                if protected_runtime:
                    raise ValueError(f"{env_name} must be explicitly configured")
                setattr(self, field_name, _generated_secret(generated_length))
                self._ephemeral_secret_fields.add(env_name)

        if self.auth_enabled and len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters when auth is enabled")
        if self.auth_enabled and _looks_placeholder_secret(self.jwt_secret_key):
            raise ValueError("JWT_SECRET_KEY must not use placeholder text")
        if self.auth_enabled and _looks_placeholder_secret(self.auth_password_pepper):
            raise ValueError("AUTH_PASSWORD_PEPPER must not use placeholder text")
        if self.export_signing_enabled and len(self.export_signing_key) < 32:
            raise ValueError(
                "EXPORT_SIGNING_KEY must be at least 32 characters when export signing is enabled"
            )
        if self.export_signing_enabled and _looks_placeholder_secret(self.export_signing_key):
            raise ValueError("EXPORT_SIGNING_KEY must not use placeholder text")
        if not self.allowed_input_base_dir.strip():
            raise ValueError("ALLOWED_INPUT_BASE_DIR must not be blank")
        if not self.allowed_output_base_dir.strip():
            raise ValueError("ALLOWED_OUTPUT_BASE_DIR must not be blank")
        if not self.allowed_template_base_dir.strip():
            raise ValueError("ALLOWED_TEMPLATE_BASE_DIR must not be blank")

        if protected_runtime:
            if not self.auth_enabled:
                raise ValueError("AUTH_ENABLED=true is required for a protected runtime")
            if not self.export_signing_enabled:
                raise ValueError("EXPORT_SIGNING_ENABLED=true is required for a protected runtime")
            if self.runtime_owner != "customer":
                raise ValueError("RUNTIME_OWNER=customer is required for a protected runtime")
            if self.runtime_workers != 1:
                raise ValueError(
                    "RUNTIME_WORKERS=1 is required while audit and login state are process-local"
                )
            if self.auth_rate_limit_mode != "upstream-enforced":
                raise ValueError(
                    "AUTH_RATE_LIMIT_MODE=upstream-enforced is required for a protected runtime"
                )
            if self.audit_storage_mode != "persistent-filesystem":
                raise ValueError(
                    "AUDIT_STORAGE_MODE=persistent-filesystem is required for a protected runtime"
                )
        return self

    def secret_posture(self) -> dict[str, object]:
        ephemeral_fields = sorted(self._ephemeral_secret_fields)
        return {
            "mode": "ephemeral-dev-only" if ephemeral_fields else "operator-supplied",
            "ephemeral_fields": ephemeral_fields,
            "rotation_owner": self.runtime_owner,
        }

    def runtime_boundary(self) -> dict[str, object]:
        protected_runtime = self.app_env.strip().lower() in PROTECTED_ENVIRONMENTS
        return {
            "delivery_mode": "customer-owned-pilot",
            "runtime_owner": self.runtime_owner,
            "supported_topology": "single-process",
            "configured_workers": self.runtime_workers,
            "rate_limit": {
                "scope": "process-local",
                "resets_on_restart": True,
                "upstream_required_for_shared_access": True,
                "upstream_configured": self.auth_rate_limit_mode == "upstream-enforced",
            },
            "audit_state": {
                "scope": "process-local-filesystem",
                "cross_process_safe": False,
                "persistent_storage_configured": (
                    self.audit_storage_mode == "persistent-filesystem"
                ),
            },
            "secrets": self.secret_posture(),
            "pilot_ready": protected_runtime,
            "production_ready": False,
            "production_blockers": [
                "customer identity integration is not included",
                "login throttling and audit hash state are not shared across processes",
                "customer monitoring, backup, retention, and recovery acceptance are required",
            ],
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
