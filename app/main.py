from __future__ import annotations

import csv
import hashlib
import hmac
import json
import os
import tempfile
import threading
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Optional
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import jwt
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.auth_schemas import CurrentUserResponse, LoginRequest, TokenResponse
from app.api.schemas import ProcessPathRequest, ProcessResponse
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.services.audit_logger import AuditLogger
from app.services.auth_service import AuthService, AuthUser
from app.services.pipeline_service import PipelineService
from app.services.speckit_loader import SpecKitLoader

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version="0.3.0")
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR)), name="assets")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
security = HTTPBearer(auto_error=False)
spec_loader = SpecKitLoader(base_path="specs")
auth_service = AuthService(settings=settings, spec_loader=spec_loader)
audit_logger = AuditLogger(audit_log_dir=settings.audit_log_dir)


class LoginAttemptGuard:
    def __init__(self, max_failures: int, window_seconds: int, lock_seconds: int) -> None:
        self.max_failures = max(1, max_failures)
        self.window_seconds = max(10, window_seconds)
        self.lock_seconds = max(1, lock_seconds)
        self._state: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def configure(self, max_failures: int, window_seconds: int, lock_seconds: int) -> None:
        with self._lock:
            self.max_failures = max(1, max_failures)
            self.window_seconds = max(10, window_seconds)
            self.lock_seconds = max(1, lock_seconds)
            self._state.clear()

    def reset(self) -> None:
        with self._lock:
            self._state.clear()

    def check_locked(self, principal: str) -> tuple[bool, int]:
        now = time.monotonic()
        with self._lock:
            entry = self._state.get(principal)
            if not entry:
                return False, 0

            lock_until = float(entry.get("lock_until", 0.0))
            if lock_until > now:
                return True, max(1, int(lock_until - now))

            failures = entry.get("failures", [])
            pruned = [ts for ts in failures if now - float(ts) <= self.window_seconds]
            if pruned:
                entry["failures"] = pruned
                entry["lock_until"] = 0.0
                self._state[principal] = entry
            else:
                self._state.pop(principal, None)

            return False, 0

    def register_failure(self, principal: str) -> dict[str, Any]:
        now = time.monotonic()
        with self._lock:
            entry = self._state.get(principal, {"failures": [], "lock_until": 0.0})
            failures = [ts for ts in entry.get("failures", []) if now - float(ts) <= self.window_seconds]
            failures.append(now)

            lock_until = float(entry.get("lock_until", 0.0))
            locked = False
            retry_after_seconds = 0
            if len(failures) >= self.max_failures:
                lock_until = now + self.lock_seconds
                locked = True
                retry_after_seconds = self.lock_seconds

            self._state[principal] = {"failures": failures, "lock_until": lock_until}
            remaining_attempts = max(0, self.max_failures - len(failures))
            return {
                "locked": locked,
                "retry_after_seconds": retry_after_seconds,
                "failure_count_in_window": len(failures),
                "remaining_attempts": remaining_attempts,
            }

    def register_success(self, principal: str) -> None:
        with self._lock:
            self._state.pop(principal, None)


login_attempt_guard = LoginAttemptGuard(
    max_failures=settings.auth_login_max_failures,
    window_seconds=settings.auth_login_window_seconds,
    lock_seconds=settings.auth_login_lock_seconds,
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


def _actor(user: Optional[AuthUser]) -> dict[str, str]:
    if user:
        return user.to_dict()
    return {"user_id": "anonymous", "role": "Anonymous"}


def _login_principal(request: Request, user_id: str) -> str:
    remote_ip = "unknown"
    if request.client and request.client.host:
        remote_ip = request.client.host
    normalized_user_id = user_id.strip().lower() or "unknown-user"
    return f"{normalized_user_id}@{remote_ip}"


def _allowed_process_roles() -> set[str]:
    return {role.strip() for role in settings.process_allowed_roles.split(",") if role.strip()}


def _sync_login_guard_with_settings() -> None:
    if (
        login_attempt_guard.max_failures != settings.auth_login_max_failures
        or login_attempt_guard.window_seconds != settings.auth_login_window_seconds
        or login_attempt_guard.lock_seconds != settings.auth_login_lock_seconds
    ):
        login_attempt_guard.configure(
            max_failures=settings.auth_login_max_failures,
            window_seconds=settings.auth_login_window_seconds,
            lock_seconds=settings.auth_login_lock_seconds,
        )


def _raise_mapped_http_error(exc: Exception, request: Request) -> None:
    request_id = getattr(request.state, "request_id", None)
    message = str(exc)
    status_code = 400

    if isinstance(exc, FileNotFoundError):
        status_code = 404
    elif isinstance(exc, PermissionError):
        status_code = 403
    elif isinstance(exc, HTTPException):
        raise exc

    raise HTTPException(
        status_code=status_code,
        detail={"message": message, "request_id": request_id},
    ) from exc


def _recent_audit_events(limit: int) -> list[dict[str, Any]]:
    audit_dir = Path(settings.audit_log_dir)
    if not audit_dir.exists():
        return []

    events: list[dict[str, Any]] = []
    files = sorted(audit_dir.glob("*.jsonl"), reverse=True)

    for file_path in files:
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        for line in reversed(lines):
            if len(events) >= limit:
                return events
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    events.append(parsed)
            except Exception:
                continue

    return events


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _audit_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    process_status = Counter()
    login_status = Counter()
    actors = Counter()
    hourly = Counter()
    process_timeline: list[dict[str, Any]] = []

    for event in reversed(events):
        event_type = str(event.get("event_type", "")).strip()
        status = str(event.get("status", "")).strip() or "unknown"
        actor = event.get("actor") or {}
        actor_key = f"{actor.get('user_id', 'unknown')} ({actor.get('role', 'unknown')})"
        actors[actor_key] += 1

        timestamp = _parse_timestamp(event.get("timestamp_utc"))

        if event_type == "auth.login":
            login_status[status] += 1
            continue

        if event_type == "pipeline.process":
            process_status[status] += 1
            details = event.get("details") or {}

            process_timeline.append(
                {
                    "timestamp_utc": event.get("timestamp_utc"),
                    "status": status,
                    "row_count": details.get("row_count"),
                    "issue_count": details.get("issue_count"),
                    "request_id": event.get("request_id"),
                }
            )

            if timestamp:
                hour_key = timestamp.strftime("%m-%d %H:00")
                hourly[hour_key] += 1

    succeeded = process_status.get("succeeded", 0)
    failed = process_status.get("failed", 0)
    finished = succeeded + failed
    success_rate = round((succeeded / finished) * 100, 2) if finished else None

    top_actors = [{"actor": name, "count": count} for name, count in actors.most_common(8)]
    process_hourly = [
        {"bucket": bucket, "count": count} for bucket, count in sorted(hourly.items())[-12:]
    ]

    return {
        "total_events": len(events),
        "process_status_counts": dict(process_status),
        "login_status_counts": dict(login_status),
        "process_success_rate": success_rate,
        "top_actors": top_actors,
        "process_hourly": process_hourly,
        "process_timeline": process_timeline[-30:],
    }


def _filter_events(
    events: list[dict[str, Any]],
    event_type: str = "",
    status: str = "",
    actor_contains: str = "",
    since_hours: Optional[int] = None,
) -> list[dict[str, Any]]:
    event_type_normalized = event_type.strip()
    status_normalized = status.strip()
    actor_query = actor_contains.strip().lower()
    cutoff = None
    if since_hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    filtered: list[dict[str, Any]] = []
    for event in events:
        if event_type_normalized and str(event.get("event_type", "")).strip() != event_type_normalized:
            continue

        if status_normalized and str(event.get("status", "")).strip() != status_normalized:
            continue

        if actor_query:
            actor = event.get("actor") or {}
            actor_text = f"{actor.get('user_id', '')} {actor.get('role', '')}".lower()
            if actor_query not in actor_text:
                continue

        if cutoff is not None:
            timestamp = _parse_timestamp(event.get("timestamp_utc"))
            if timestamp is None or timestamp < cutoff:
                continue

        filtered.append(event)

    return filtered


def _audit_anomalies(events: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    last_24h_cutoff = now - timedelta(hours=24)

    process_total_24h = 0
    process_failed_24h = 0
    login_failed_24h = 0
    consecutive_failed_processes = 0
    max_consecutive_failed_processes = 0

    process_events_desc = [
        event for event in events if str(event.get("event_type", "")).strip() == "pipeline.process"
    ]

    for event in process_events_desc:
        status = str(event.get("status", "")).strip()
        if status == "failed":
            consecutive_failed_processes += 1
            max_consecutive_failed_processes = max(
                max_consecutive_failed_processes, consecutive_failed_processes
            )
        elif status == "succeeded":
            consecutive_failed_processes = 0

    for event in events:
        timestamp = _parse_timestamp(event.get("timestamp_utc"))
        if timestamp is None or timestamp < last_24h_cutoff:
            continue

        event_type = str(event.get("event_type", "")).strip()
        status = str(event.get("status", "")).strip()

        if event_type == "auth.login" and status == "failed":
            login_failed_24h += 1

        if event_type == "pipeline.process" and status in {"succeeded", "failed"}:
            process_total_24h += 1
            if status == "failed":
                process_failed_24h += 1

    process_failure_rate_24h = (
        round((process_failed_24h / process_total_24h) * 100, 2) if process_total_24h else None
    )

    flags: list[str] = []
    if login_failed_24h >= 5:
        flags.append("high_login_failure_24h")
    if process_failure_rate_24h is not None and process_total_24h >= 10 and process_failure_rate_24h >= 30:
        flags.append("high_process_failure_rate_24h")
    if max_consecutive_failed_processes >= 3:
        flags.append("consecutive_process_failures")

    return {
        "login_failed_24h": login_failed_24h,
        "process_failed_24h": process_failed_24h,
        "process_total_24h": process_total_24h,
        "process_failure_rate_24h": process_failure_rate_24h,
        "max_consecutive_failed_processes": max_consecutive_failed_processes,
        "flags": flags,
    }


def _build_applied_filters(
    event_type: str,
    status: str,
    actor_contains: str,
    since_hours: Optional[int],
) -> dict[str, Any]:
    return {
        "event_type": event_type or None,
        "status": status or None,
        "actor_contains": actor_contains or None,
        "since_hours": since_hours,
    }


def _audit_events_to_csv(events: list[dict[str, Any]]) -> str:
    field_names = [
        "timestamp_utc",
        "event_type",
        "status",
        "actor_user_id",
        "actor_role",
        "request_id",
        "summary",
        "row_count",
        "issue_count",
        "reason",
        "error",
    ]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=field_names)
    writer.writeheader()

    for event in events:
        actor = event.get("actor") or {}
        details = event.get("details") or {}
        summary = (
            details.get("reason")
            or details.get("error")
            or f"row_count={details.get('row_count', '-')}, issue_count={details.get('issue_count', '-')}"
        )

        writer.writerow(
            {
                "timestamp_utc": event.get("timestamp_utc") or "",
                "event_type": event.get("event_type") or "",
                "status": event.get("status") or "",
                "actor_user_id": actor.get("user_id") or "",
                "actor_role": actor.get("role") or "",
                "request_id": event.get("request_id") or "",
                "summary": summary,
                "row_count": details.get("row_count", ""),
                "issue_count": details.get("issue_count", ""),
                "reason": details.get("reason") or "",
                "error": details.get("error") or "",
            }
        )

    return output.getvalue()


def _export_signature_headers(payload_bytes: bytes) -> dict[str, str]:
    sha256_hex = hashlib.sha256(payload_bytes).hexdigest()
    headers: dict[str, str] = {
        "X-Export-SHA256": sha256_hex,
        "X-Export-Signature-Alg": "none",
        "X-Export-Signature-Key-Id": "none",
        "X-Export-Signature": "",
    }

    if settings.export_signing_enabled:
        signature = hmac.new(
            settings.export_signing_key.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        headers["X-Export-Signature-Alg"] = "hmac-sha256"
        headers["X-Export-Signature-Key-Id"] = settings.export_signing_key_id
        headers["X-Export-Signature"] = signature

    return headers


def _signature_manifest_for_payload(
    payload_file_name: str,
    endpoint: str,
    applied_filters: dict[str, Any],
    payload_bytes: bytes,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    headers = _export_signature_headers(payload_bytes)
    manifest = {
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "payload_file": payload_file_name,
        "applied_filters": applied_filters,
        "signature": {
            "algorithm": headers.get("X-Export-Signature-Alg", "none"),
            "key_id": headers.get("X-Export-Signature-Key-Id", "none"),
            "sha256": headers.get("X-Export-SHA256", ""),
            "value": headers.get("X-Export-Signature", ""),
        },
    }
    if extra:
        manifest.update(extra)
    return manifest


def _build_signed_bundle(
    payload_file_name: str,
    payload_bytes: bytes,
    manifest: dict[str, Any],
) -> bytes:
    base = payload_file_name.rsplit(".", maxsplit=1)[0]
    manifest_file_name = f"{base}.sig.json"

    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr(payload_file_name, payload_bytes)
        zip_file.writestr(
            manifest_file_name,
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
    return buffer.getvalue()


def _service_readiness() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    try:
        spec_loader.load_contract("default")
        spec_loader.load_profile("default")
        spec_loader.load_template_profile("default")
        checks.append({"name": "specs", "status": "ok", "detail": "default spec set loaded"})
    except Exception as exc:
        checks.append({"name": "specs", "status": "failed", "detail": str(exc)})

    audit_dir = Path(settings.audit_log_dir)
    try:
        audit_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=audit_dir, prefix=".writecheck-", delete=True) as handle:
            handle.write(b"ok")
        checks.append({"name": "audit_log_dir", "status": "ok", "detail": str(audit_dir.resolve())})
    except Exception as exc:
        checks.append({"name": "audit_log_dir", "status": "failed", "detail": str(exc)})

    if settings.export_signing_enabled and len(settings.export_signing_key) >= 32:
        checks.append(
            {
                "name": "export_signing",
                "status": "ok",
                "detail": f"enabled (key_id={settings.export_signing_key_id})",
            }
        )
    elif settings.export_signing_enabled:
        checks.append(
            {
                "name": "export_signing",
                "status": "failed",
                "detail": "enabled but key length is too short",
            }
        )
    else:
        checks.append({"name": "export_signing", "status": "skipped", "detail": "disabled"})

    if settings.enable_llm:
        try:
            with httpx.Client(timeout=1.5) as client:
                response = client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            if response.status_code == 200:
                checks.append(
                    {
                        "name": "llm_connectivity",
                        "status": "ok",
                        "detail": f"reachable ({settings.ollama_base_url})",
                    }
                )
            else:
                checks.append(
                    {
                        "name": "llm_connectivity",
                        "status": "failed",
                        "detail": f"unexpected status={response.status_code}",
                    }
                )
        except Exception as exc:
            checks.append(
                {
                    "name": "llm_connectivity",
                    "status": "failed",
                    "detail": str(exc),
                }
            )
    else:
        checks.append({"name": "llm_connectivity", "status": "skipped", "detail": "LLM disabled"})

    failed_checks = [check["name"] for check in checks if check.get("status") == "failed"]
    overall_status = "healthy" if not failed_checks else "degraded"

    return {
        "overall_status": overall_status,
        "failed_checks": failed_checks,
        "checks": checks,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _is_hex_string(value: str, expected_len: int) -> bool:
    if len(value) != expected_len:
        return False
    return all(ch in "0123456789abcdef" for ch in value.lower())


async def _read_upload_bytes(upload: UploadFile, max_bytes: int, label: str) -> bytes:
    total_bytes = 0
    chunks: list[bytes] = []

    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{label} exceeds max size limit ({settings.max_upload_mb}MB)",
            )
        chunks.append(chunk)

    return b"".join(chunks)


def _parse_signature_manifest(raw_bytes: bytes) -> dict[str, Any]:
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Signature manifest must be UTF-8 JSON") from exc

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature manifest JSON") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="Signature manifest must be an object")

    signature = parsed.get("signature")
    if not isinstance(signature, dict):
        raise HTTPException(status_code=400, detail="Signature manifest missing 'signature' object")

    algorithm = str(signature.get("algorithm", "")).strip().lower()
    key_id = str(signature.get("key_id", "")).strip()
    sha256_hex = str(signature.get("sha256", "")).strip().lower()
    signature_hex = str(signature.get("value", "")).strip().lower()

    if not _is_hex_string(sha256_hex, expected_len=64):
        raise HTTPException(status_code=400, detail="Signature manifest contains invalid sha256")

    payload_file_name = parsed.get("payload_file")
    if payload_file_name is not None and not isinstance(payload_file_name, str):
        raise HTTPException(status_code=400, detail="Signature manifest 'payload_file' must be a string")

    return {
        "algorithm": algorithm,
        "key_id": key_id,
        "sha256": sha256_hex,
        "signature": signature_hex,
        "payload_file": payload_file_name or "",
    }


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthUser:
    if not settings.auth_enabled:
        return AuthUser(user_id="local-system", role="System")

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        return auth_service.verify_token(credentials.credentials)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def require_process_user(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not settings.auth_enabled:
        return current_user

    allowed_roles = _allowed_process_roles()
    if allowed_roles and current_user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Insufficient role for processing endpoint")
    return current_user


def require_audit_user(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not settings.auth_enabled:
        return current_user

    if current_user.role not in {"Admin", "Auditor"}:
        raise HTTPException(status_code=403, detail="Insufficient role for audit endpoint")
    return current_user


@app.get("/", response_class=HTMLResponse)
def ui_home(request: Request) -> HTMLResponse:
    ui_config = {
        "auth_enabled": settings.auth_enabled,
        "process_allowed_roles": sorted(_allowed_process_roles()),
        "max_upload_mb": settings.max_upload_mb,
        "export_signing": {
            "enabled": settings.export_signing_enabled,
            "key_id": settings.export_signing_key_id if settings.export_signing_enabled else None,
        },
        "ui_defaults": {
            "language": "ko",
            "theme": "light",
            "brand": "aqua",
        },
        "default_paths": {
            "input_path": "examples/input/sample_projects.xlsx",
            "output_dir": "examples/output",
            "contract_name": "default",
            "profile_name": "default",
            "template_name": "default",
            "template_path": "examples/input/sample_report_template.txt",
        },
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"ui_config_json": json.dumps(ui_config, ensure_ascii=False)},
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "llm_enabled": settings.enable_llm,
        "auth_enabled": settings.auth_enabled,
        "auth_login_guard": {
            "max_failures": login_attempt_guard.max_failures,
            "window_seconds": login_attempt_guard.window_seconds,
            "lock_seconds": login_attempt_guard.lock_seconds,
        },
        "process_allowed_roles": sorted(_allowed_process_roles()),
        "audit_log_dir": settings.audit_log_dir,
        "export_signing_enabled": settings.export_signing_enabled,
        "export_signing_key_id": settings.export_signing_key_id if settings.export_signing_enabled else None,
    }


@app.get("/ops/readiness")
def ops_readiness(_current_user: AuthUser = Depends(require_audit_user)) -> dict[str, Any]:
    return _service_readiness()


@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request) -> TokenResponse:
    if not settings.auth_enabled:
        system_user = AuthUser(user_id="local-system", role="System")
        token, expires_at_utc = auth_service.issue_access_token(system_user)
        return TokenResponse(
            access_token=token,
            expires_at_utc=expires_at_utc,
            user_id=system_user.user_id,
            role=system_user.role,
        )

    _sync_login_guard_with_settings()
    principal = _login_principal(request, req.user_id)
    locked, retry_after_seconds = login_attempt_guard.check_locked(principal)
    if locked:
        audit_logger.log_event(
            event_type="auth.login",
            status="failed",
            actor={"user_id": req.user_id, "role": "unknown"},
            request_id=request.state.request_id,
            details={
                "reason": "rate_limited",
                "retry_after_seconds": retry_after_seconds,
            },
        )
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Too many failed login attempts",
                "retry_after_seconds": retry_after_seconds,
                "request_id": request.state.request_id,
            },
        )

    user = auth_service.authenticate(req.user_id, req.password)
    if not user:
        failure_state = login_attempt_guard.register_failure(principal)
        audit_logger.log_event(
            event_type="auth.login",
            status="failed",
            actor={"user_id": req.user_id, "role": "unknown"},
            request_id=request.state.request_id,
            details={"reason": "invalid_credentials", **failure_state},
        )
        if failure_state["locked"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Too many failed login attempts",
                    "retry_after_seconds": failure_state["retry_after_seconds"],
                    "request_id": request.state.request_id,
                },
            )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    login_attempt_guard.register_success(principal)

    token, expires_at_utc = auth_service.issue_access_token(user)

    audit_logger.log_event(
        event_type="auth.login",
        status="succeeded",
        actor=user.to_dict(),
        request_id=request.state.request_id,
        details={"expires_at_utc": expires_at_utc},
    )

    return TokenResponse(
        access_token=token,
        expires_at_utc=expires_at_utc,
        user_id=user.user_id,
        role=user.role,
    )


@app.get("/auth/guard/state")
def auth_guard_state(_current_user: AuthUser = Depends(require_audit_user)) -> dict[str, Any]:
    # Expose current config only; attempt state is intentionally not returned.
    return {
        "enabled": settings.auth_enabled,
        "max_failures": login_attempt_guard.max_failures,
        "window_seconds": login_attempt_guard.window_seconds,
        "lock_seconds": login_attempt_guard.lock_seconds,
    }


@app.get("/auth/me", response_model=CurrentUserResponse)
def me(current_user: AuthUser = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(user_id=current_user.user_id, role=current_user.role)


@app.get("/ops/audit/recent")
def ops_audit_recent(
    limit: int = Query(default=30, ge=1, le=200),
    event_type: str = Query(default="", max_length=64),
    status: str = Query(default="", max_length=32),
    actor_contains: str = Query(default="", max_length=120),
    since_hours: Optional[int] = Query(default=None, ge=1, le=2160),
    _current_user: AuthUser = Depends(require_audit_user),
) -> dict:
    read_limit = (
        max(limit, 500) if since_hours is not None or event_type or status or actor_contains else limit
    )
    events = _recent_audit_events(limit=read_limit)
    filtered = _filter_events(
        events=events,
        event_type=event_type,
        status=status,
        actor_contains=actor_contains,
        since_hours=since_hours,
    )
    sliced = filtered[:limit]
    return {
        "count": len(sliced),
        "events": sliced,
        "applied_filters": _build_applied_filters(
            event_type=event_type,
            status=status,
            actor_contains=actor_contains,
            since_hours=since_hours,
        ),
    }


@app.get("/ops/audit/summary")
def ops_audit_summary(
    limit: int = Query(default=120, ge=10, le=500),
    event_type: str = Query(default="", max_length=64),
    status: str = Query(default="", max_length=32),
    actor_contains: str = Query(default="", max_length=120),
    since_hours: Optional[int] = Query(default=None, ge=1, le=2160),
    _current_user: AuthUser = Depends(require_audit_user),
) -> dict:
    events = _recent_audit_events(limit=limit)
    filtered = _filter_events(
        events=events,
        event_type=event_type,
        status=status,
        actor_contains=actor_contains,
        since_hours=since_hours,
    )
    return {
        "count": len(filtered),
        "summary": _audit_summary(filtered),
        "anomalies": _audit_anomalies(filtered),
        "applied_filters": _build_applied_filters(
            event_type=event_type,
            status=status,
            actor_contains=actor_contains,
            since_hours=since_hours,
        ),
    }


@app.get("/ops/audit/export/summary")
def ops_audit_export_summary(
    limit: int = Query(default=120, ge=10, le=500),
    event_type: str = Query(default="", max_length=64),
    status: str = Query(default="", max_length=32),
    actor_contains: str = Query(default="", max_length=120),
    since_hours: Optional[int] = Query(default=None, ge=1, le=2160),
    _current_user: AuthUser = Depends(require_audit_user),
) -> Response:
    events = _recent_audit_events(limit=limit)
    filtered = _filter_events(
        events=events,
        event_type=event_type,
        status=status,
        actor_contains=actor_contains,
        since_hours=since_hours,
    )
    exported_at_utc = datetime.now(timezone.utc).isoformat()
    applied_filters = _build_applied_filters(
        event_type=event_type,
        status=status,
        actor_contains=actor_contains,
        since_hours=since_hours,
    )
    payload = {
        "dataset": "audit.summary",
        "exported_at_utc": exported_at_utc,
        "count": len(filtered),
        "summary": _audit_summary(filtered),
        "anomalies": _audit_anomalies(filtered),
        "applied_filters": applied_filters,
    }
    payload_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    payload_bytes = payload_text.encode("utf-8")
    headers = _export_signature_headers(payload_bytes)
    file_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    headers["Content-Disposition"] = f'attachment; filename="audit-summary-{file_stamp}.json"'
    return Response(
        content=payload_text,
        media_type="application/json; charset=utf-8",
        headers=headers,
    )


@app.get("/ops/audit/export/summary.bundle.zip")
def ops_audit_export_summary_bundle(
    limit: int = Query(default=120, ge=10, le=500),
    event_type: str = Query(default="", max_length=64),
    status: str = Query(default="", max_length=32),
    actor_contains: str = Query(default="", max_length=120),
    since_hours: Optional[int] = Query(default=None, ge=1, le=2160),
    _current_user: AuthUser = Depends(require_audit_user),
) -> Response:
    events = _recent_audit_events(limit=limit)
    filtered = _filter_events(
        events=events,
        event_type=event_type,
        status=status,
        actor_contains=actor_contains,
        since_hours=since_hours,
    )
    applied_filters = _build_applied_filters(
        event_type=event_type,
        status=status,
        actor_contains=actor_contains,
        since_hours=since_hours,
    )
    payload = {
        "dataset": "audit.summary",
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(filtered),
        "summary": _audit_summary(filtered),
        "anomalies": _audit_anomalies(filtered),
        "applied_filters": applied_filters,
    }
    payload_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    payload_bytes = payload_text.encode("utf-8")

    file_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload_file_name = f"audit-summary-{file_stamp}.json"
    manifest = _signature_manifest_for_payload(
        payload_file_name=payload_file_name,
        endpoint="/ops/audit/export/summary.bundle.zip",
        applied_filters=applied_filters,
        payload_bytes=payload_bytes,
        extra={"count": len(filtered)},
    )
    bundle_bytes = _build_signed_bundle(
        payload_file_name=payload_file_name,
        payload_bytes=payload_bytes,
        manifest=manifest,
    )
    headers = {
        "Content-Disposition": f'attachment; filename="audit-summary-{file_stamp}.bundle.zip"',
        "X-Bundle-SHA256": hashlib.sha256(bundle_bytes).hexdigest(),
    }
    return Response(content=bundle_bytes, media_type="application/zip", headers=headers)


@app.get("/ops/audit/export/recent.csv")
def ops_audit_export_recent_csv(
    limit: int = Query(default=200, ge=1, le=1000),
    event_type: str = Query(default="", max_length=64),
    status: str = Query(default="", max_length=32),
    actor_contains: str = Query(default="", max_length=120),
    since_hours: Optional[int] = Query(default=None, ge=1, le=2160),
    _current_user: AuthUser = Depends(require_audit_user),
) -> Response:
    read_limit = (
        max(limit, 500) if since_hours is not None or event_type or status or actor_contains else limit
    )
    events = _recent_audit_events(limit=read_limit)
    filtered = _filter_events(
        events=events,
        event_type=event_type,
        status=status,
        actor_contains=actor_contains,
        since_hours=since_hours,
    )
    csv_text = _audit_events_to_csv(filtered[:limit])
    csv_bytes = csv_text.encode("utf-8")
    headers = _export_signature_headers(csv_bytes)
    file_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    headers["Content-Disposition"] = f'attachment; filename="audit-recent-{file_stamp}.csv"'
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


@app.get("/ops/audit/export/recent.bundle.zip")
def ops_audit_export_recent_bundle(
    limit: int = Query(default=200, ge=1, le=1000),
    event_type: str = Query(default="", max_length=64),
    status: str = Query(default="", max_length=32),
    actor_contains: str = Query(default="", max_length=120),
    since_hours: Optional[int] = Query(default=None, ge=1, le=2160),
    _current_user: AuthUser = Depends(require_audit_user),
) -> Response:
    read_limit = (
        max(limit, 500) if since_hours is not None or event_type or status or actor_contains else limit
    )
    events = _recent_audit_events(limit=read_limit)
    filtered = _filter_events(
        events=events,
        event_type=event_type,
        status=status,
        actor_contains=actor_contains,
        since_hours=since_hours,
    )
    applied_filters = _build_applied_filters(
        event_type=event_type,
        status=status,
        actor_contains=actor_contains,
        since_hours=since_hours,
    )
    selected = filtered[:limit]
    csv_text = _audit_events_to_csv(selected)
    csv_bytes = csv_text.encode("utf-8")

    file_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload_file_name = f"audit-recent-{file_stamp}.csv"
    manifest = _signature_manifest_for_payload(
        payload_file_name=payload_file_name,
        endpoint="/ops/audit/export/recent.bundle.zip",
        applied_filters=applied_filters,
        payload_bytes=csv_bytes,
        extra={"row_count": len(selected)},
    )
    bundle_bytes = _build_signed_bundle(
        payload_file_name=payload_file_name,
        payload_bytes=csv_bytes,
        manifest=manifest,
    )
    headers = {
        "Content-Disposition": f'attachment; filename="audit-recent-{file_stamp}.bundle.zip"',
        "X-Bundle-SHA256": hashlib.sha256(bundle_bytes).hexdigest(),
    }
    return Response(content=bundle_bytes, media_type="application/zip", headers=headers)


@app.post("/ops/audit/export/verify")
async def ops_audit_export_verify(
    payload_file: UploadFile = File(...),
    signature_file: UploadFile = File(...),
    _current_user: AuthUser = Depends(require_audit_user),
) -> dict[str, Any]:
    max_bytes = settings.max_upload_mb * 1024 * 1024

    payload_bytes = await _read_upload_bytes(payload_file, max_bytes=max_bytes, label="Payload file")
    signature_bytes = await _read_upload_bytes(signature_file, max_bytes=max_bytes, label="Signature file")
    manifest = _parse_signature_manifest(signature_bytes)

    computed_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    provided_sha256 = manifest["sha256"]
    hash_match = hmac.compare_digest(provided_sha256, computed_sha256)

    provided_algorithm = manifest["algorithm"]
    provided_key_id = manifest["key_id"]
    provided_signature = manifest["signature"]
    declared_payload_name = manifest["payload_file"]
    actual_payload_name = payload_file.filename or ""

    algorithm_supported = provided_algorithm in {"hmac-sha256", "none"}
    payload_name_match = not declared_payload_name or declared_payload_name == actual_payload_name

    key_id_match: Optional[bool] = None
    signature_match: bool = False
    signature_format_valid: Optional[bool] = None

    if algorithm_supported and provided_algorithm == "none":
        key_id_match = provided_key_id in {"", "none"}
        signature_format_valid = provided_signature == ""
        signature_match = signature_format_valid
    elif algorithm_supported and provided_algorithm == "hmac-sha256":
        key_id_match = provided_key_id == settings.export_signing_key_id
        signature_format_valid = _is_hex_string(provided_signature, expected_len=64)
        expected_signature = hmac.new(
            settings.export_signing_key.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        signature_match = signature_format_valid and hmac.compare_digest(provided_signature, expected_signature)
    else:
        key_id_match = False
        signature_format_valid = False
        signature_match = False

    overall_valid = bool(
        hash_match
        and algorithm_supported
        and payload_name_match
        and (key_id_match is True)
        and signature_match
    )

    failed_checks: list[str] = []
    if not hash_match:
        failed_checks.append("hash_match")
    if not algorithm_supported:
        failed_checks.append("algorithm_supported")
    if not payload_name_match:
        failed_checks.append("payload_name_match")
    if key_id_match is not True:
        failed_checks.append("key_id_match")
    if signature_format_valid is not True:
        failed_checks.append("signature_format_valid")
    if not signature_match:
        failed_checks.append("signature_match")

    return {
        "overall_valid": overall_valid,
        "checks": {
            "hash_match": hash_match,
            "algorithm_supported": algorithm_supported,
            "payload_name_match": payload_name_match,
            "key_id_match": key_id_match,
            "signature_format_valid": signature_format_valid,
            "signature_match": signature_match,
        },
        "provided": {
            "payload_name": actual_payload_name or None,
            "declared_payload_name": declared_payload_name or None,
            "algorithm": provided_algorithm or None,
            "key_id": provided_key_id or None,
            "sha256": provided_sha256,
            "signature_length": len(provided_signature),
            "payload_size_bytes": len(payload_bytes),
        },
        "computed": {
            "sha256": computed_sha256,
        },
        "expected": {
            "algorithm": "hmac-sha256" if settings.export_signing_enabled else "none",
            "key_id": settings.export_signing_key_id if settings.export_signing_enabled else "none",
        },
        "failed_checks": failed_checks,
    }


@app.post("/process/path", response_model=ProcessResponse)
def process_path(
    req: ProcessPathRequest,
    request: Request,
    current_user: AuthUser = Depends(require_process_user),
) -> ProcessResponse:
    service = PipelineService(settings=settings, audit_logger=audit_logger)
    try:
        outcome = service.process(
            input_path=req.input_path,
            output_dir=req.output_dir,
            contract_name=req.contract_name,
            profile_name=req.profile_name,
            template_name=req.template_name,
            template_path=req.template_path,
            actor=_actor(current_user),
            request_id=request.state.request_id,
        )
    except Exception as exc:
        _raise_mapped_http_error(exc, request)

    return ProcessResponse(success=True, outcome=outcome.to_dict())


@app.post("/process/file", response_model=ProcessResponse)
async def process_upload(
    request: Request,
    file: UploadFile = File(...),
    output_dir: str = "examples/output",
    contract_name: str = "default",
    profile_name: str = "default",
    template_name: str = "default",
    template_path: str = "",
    current_user: AuthUser = Depends(require_process_user),
) -> ProcessResponse:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")

    service = PipelineService(settings=settings, audit_logger=audit_logger)
    temp_path = ""

    try:
        max_bytes = settings.max_upload_mb * 1024 * 1024
        total_bytes = 0
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            temp_path = temp_file.name
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Uploaded file exceeds max size limit ({settings.max_upload_mb}MB)",
                    )
                temp_file.write(chunk)

        outcome = service.process(
            input_path=temp_path,
            output_dir=output_dir,
            contract_name=contract_name,
            profile_name=profile_name,
            template_name=template_name,
            template_path=template_path or None,
            actor=_actor(current_user),
            request_id=request.state.request_id,
        )
    except Exception as exc:
        _raise_mapped_http_error(exc, request)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    return ProcessResponse(success=True, outcome=outcome.to_dict())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=False)
