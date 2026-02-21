import secrets
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    app_name: str = "secure-xl2hwp-local"
    app_env: str = "dev"
    log_level: str = "INFO"

    ollama_base_url: str = "http://127.0.0.1:11434"
    llm_primary_model: str = "qwen2.5:7b"
    llm_fallback_model: str = "qwen2.5:14b"
    llm_timeout_seconds: int = Field(default=45, ge=1)
    llm_unavailable_cooldown_seconds: int = Field(default=20, ge=0)
    enable_llm: bool = True

    auth_enabled: bool = True
    jwt_secret_key: str = Field(default_factory=lambda: _generated_secret(48))
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = Field(default=120, ge=1)
    auth_password_pepper: str = Field(default_factory=lambda: _generated_secret(24))
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
    export_signing_key: str = Field(default_factory=lambda: _generated_secret(48))

    @model_validator(mode="after")
    def validate_security(self) -> "Settings":
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
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
