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
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
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
from app.services.template_engine import HancomTemplateEngine

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
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
template_engine = HancomTemplateEngine()
auth_service = AuthService(settings=settings, spec_loader=spec_loader)
audit_logger = AuditLogger(audit_log_dir=settings.audit_log_dir)


class LoginAttemptGuard:
    """In-memory rate limiter for login attempts.

    LIMITATION: ``threading.Lock`` only serialises access across threads
    within a **single process**.  When the application is deployed behind a
    multi-process server (e.g. ``gunicorn --workers N``, or multiple uvicorn
    processes), each worker maintains its own independent ``_state`` dict and
    lock, so an attacker can spread brute-force attempts across workers and
    bypass the per-principal limit.

    For production multi-worker deployments, replace this guard with one of:
      * A Redis-backed sliding-window counter (e.g. ``redis-py`` + Lua script)
      * A file-based lock using ``fcntl.flock`` / ``msvcrt.locking`` (slower
        but zero-dependency)
      * An external rate-limiting middleware (e.g. Cloudflare, nginx
        ``limit_req``)
    """

    def __init__(self, max_failures: int, window_seconds: int, lock_seconds: int) -> None:
        self.max_failures = max(1, max_failures)
        self.window_seconds = max(10, window_seconds)
        self.lock_seconds = max(1, lock_seconds)
        self._state: dict[str, dict[str, Any]] = {}
        # NOTE: threading.Lock is NOT safe across process boundaries.
        # See class docstring for multi-worker alternatives.
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

PROCESS_REPORT_SCHEMA = "secure-xl2hwp-process-report-v1"
SERVICE_BRIEF_CONTRACT = "secure-xl2hwp-service-brief-v1"
ARCHITECTURE_PACK_CONTRACT = "secure-xl2hwp-architecture-pack-v1"
RUNTIME_SCORECARD_CONTRACT = "secure-xl2hwp-runtime-scorecard-v1"
SERVICE_BRIEF_ROUTES = [
    "/health",
    "/ops/service-brief",
    "/ops/runtime-scorecard",
    "/ops/template-drift-preview",
    "/ops/export-verification-pack",
    "/ops/offline-deployment-pack",
    "/ops/architecture-pack",
    "/ops/schema/process-report",
    "/ops/readiness",
    "/auth/login",
    "/process/path",
    "/process/file",
    "/ops/audit/summary",
]


def _template_drift_preview_payload() -> dict[str, Any]:
    template_path = _resolve_repo_path(
        str(Path(settings.allowed_template_base_dir) / "sample_report_template.txt")
    )
    template_profile = spec_loader.load_template_profile("default")
    contract = spec_loader.load_contract("default")

    detected_placeholders = template_engine.detect_placeholders(template_path)
    configured_rules = set(template_profile.placeholder_rules.keys())
    table_placeholders = {section.placeholder for section in template_profile.table_sections}
    missing_rules = sorted(set(detected_placeholders) - configured_rules)
    missing_table_rules = sorted(set(detected_placeholders) - configured_rules - table_placeholders)
    affected_fields = sorted(
        {
            str(rule.source).split(".", 1)[-1]
            for rule in template_profile.placeholder_rules.values()
            if "." in str(rule.source)
        }
    )[:8]

    return {
        "status": "ok",
        "service": "secure-xl2hwp-local",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema": "secure-xl2hwp-template-drift-preview-v1",
        "summary": {
            "template_name": template_profile.template_name,
            "detected_placeholders": len(detected_placeholders),
            "configured_rules": len(configured_rules),
            "missing_rules": len(missing_rules),
            "missing_table_rules": len(missing_table_rules),
        },
        "items": {
            "detected_placeholders": detected_placeholders,
            "missing_rules": missing_rules,
            "missing_table_rules": missing_table_rules,
            "affected_fields": affected_fields,
            "contract_dataset": contract.dataset,
        },
        "architecture_actions": [
            "Review missing placeholder rules before exporting regulated templates.",
            "Treat missing table placeholders as re-review blockers, not cosmetic gaps.",
            "Verify signed export bundles only after template drift items are resolved.",
        ],
        "links": {
            "template_drift_preview": "/ops/template-drift-preview",
            "export_verification_pack": "/ops/export-verification-pack",
            "service_brief": "/ops/service-brief",
            "runtime_scorecard": "/ops/runtime-scorecard",
            "architecture_pack": "/ops/architecture-pack",
        },
    }


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


def _absolute_repo_path(path_value: str) -> str:
    """Normalize a path lexically without touching attacker-selected filesystem locations."""
    candidate = (
        path_value
        if os.path.isabs(path_value)
        else os.path.join(str(REPO_ROOT), path_value)
    )
    return os.path.normcase(os.path.abspath(candidate))


def _path_prefix(path_value: str) -> str:
    return path_value.rstrip(os.sep) + os.sep


def _resolve_repo_path(path_value: str) -> Path:
    absolute_path = _absolute_repo_path(path_value)
    return Path(os.path.normcase(os.path.realpath(absolute_path)))


def _assert_path_within_base(path_value: str, base_dir_value: str, field_name: str) -> Path:
    # First perform a lexical boundary check. This prevents an absolute/UNC path outside
    # the configured base from being resolved at all (important on Windows, where
    # resolving an attacker-selected UNC path can initiate an outbound network access).
    target_lexical = _absolute_repo_path(path_value)
    base_lexical = _absolute_repo_path(base_dir_value)
    if target_lexical == base_lexical:
        target_lexical = base_lexical
    elif not target_lexical.startswith(_path_prefix(base_lexical)):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must stay under configured base directory: {base_lexical}",
        )

    # Resolve symlinks only after the lexical check, then enforce the boundary again
    # so a link located under an allowed directory cannot escape that directory.
    target = os.path.normcase(os.path.realpath(target_lexical))
    base_dir = os.path.normcase(os.path.realpath(base_lexical))
    if target == base_dir:
        return Path(base_dir)
    if not target.startswith(_path_prefix(base_dir)):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must stay under configured base directory: {base_dir}",
        )
    return Path(target)


def _validate_process_path_request(
    *,
    input_path: str,
    output_dir: str,
    template_path: Optional[str],
) -> tuple[str, str, Optional[str]]:
    safe_input_path = _assert_path_within_base(
        input_path,
        settings.allowed_input_base_dir,
        "input_path",
    )
    safe_output_dir = _assert_path_within_base(
        output_dir,
        settings.allowed_output_base_dir,
        "output_dir",
    )
    safe_output_dir.mkdir(parents=True, exist_ok=True)

    safe_template_path: Optional[Path] = None
    if template_path:
        safe_template_path = _assert_path_within_base(
            template_path,
            settings.allowed_template_base_dir,
            "template_path",
        )

    return str(safe_input_path), str(safe_output_dir), str(safe_template_path) if safe_template_path else None


def _validate_upload_request_paths(
    *,
    output_dir: str,
    template_path: Optional[str],
) -> tuple[str, Optional[str]]:
    safe_output_dir = _assert_path_within_base(
        output_dir,
        settings.allowed_output_base_dir,
        "output_dir",
    )
    safe_output_dir.mkdir(parents=True, exist_ok=True)

    safe_template_path: Optional[Path] = None
    if template_path:
        safe_template_path = _assert_path_within_base(
            template_path,
            settings.allowed_template_base_dir,
            "template_path",
        )

    return str(safe_output_dir), str(safe_template_path) if safe_template_path else None


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


def _user_registry_relative_path() -> str:
    return str(Path("specs") / "security" / f"{settings.user_registry_name}.yaml")


def _auth_bootstrap_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "required": False,
        "total_users": 0,
        "active_users": 0,
        "registry_path": _user_registry_relative_path(),
        "load_error": False,
    }
    if not settings.auth_enabled:
        return snapshot

    try:
        registry = spec_loader.load_user_registry(settings.user_registry_name)
    except (OSError, ValueError, KeyError):
        snapshot["required"] = True
        snapshot["load_error"] = True
        return snapshot

    total_users = len(registry.users)
    active_users = sum(1 for user in registry.users if user.active)
    snapshot["total_users"] = total_users
    snapshot["active_users"] = active_users
    snapshot["required"] = active_users == 0
    return snapshot


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
        except OSError:
            continue

        for line in reversed(lines):
            if len(events) >= limit:
                return events
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    events.append(parsed)
            except (json.JSONDecodeError, ValueError):
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

    hash_chain_checked = 0
    hash_chain_broken = 0
    hash_chain_legacy_events = 0
    previous_hash = "GENESIS"
    ordered_events = list(reversed(events))
    for event in ordered_events:
        current_event_hash = str(event.get("event_hash", "")).strip()
        current_prev_hash = str(event.get("prev_hash", "")).strip()
        if len(current_event_hash) != 64 or not current_prev_hash:
            hash_chain_legacy_events += 1
            continue
        if current_prev_hash != previous_hash:
            hash_chain_broken += 1
        previous_hash = current_event_hash or previous_hash
        hash_chain_checked += 1

    for event in ordered_events:
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
        "hash_chain_checked": hash_chain_checked,
        "hash_chain_broken": hash_chain_broken,
        "hash_chain_legacy_events": hash_chain_legacy_events,
        "hash_chain_valid": hash_chain_checked == 0 or hash_chain_broken == 0,
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
    runtime_boundary = settings.runtime_boundary()

    try:
        spec_loader.load_contract("default")
        spec_loader.load_profile("default")
        spec_loader.load_template_profile("default")
        checks.append({"name": "specs", "status": "ok", "detail": "default spec set loaded"})
    except (OSError, ValueError, KeyError) as exc:
        checks.append({"name": "specs", "status": "failed", "detail": str(exc)})

    audit_dir = Path(settings.audit_log_dir)
    try:
        audit_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=audit_dir, prefix=".writecheck-", delete=True) as handle:
            handle.write(b"ok")
        checks.append({"name": "audit_log_dir", "status": "ok", "detail": str(audit_dir.resolve())})
    except OSError as exc:
        checks.append({"name": "audit_log_dir", "status": "failed", "detail": str(exc)})

    input_base_dir = _resolve_repo_path(settings.allowed_input_base_dir)
    if input_base_dir.exists():
        checks.append({"name": "input_base_dir", "status": "ok", "detail": str(input_base_dir)})
    else:
        checks.append(
            {
                "name": "input_base_dir",
                "status": "failed",
                "detail": f"missing path: {input_base_dir}",
            }
        )

    template_base_dir = _resolve_repo_path(settings.allowed_template_base_dir)
    if template_base_dir.exists():
        checks.append({"name": "template_base_dir", "status": "ok", "detail": str(template_base_dir)})
    else:
        checks.append(
            {
                "name": "template_base_dir",
                "status": "failed",
                "detail": f"missing path: {template_base_dir}",
            }
        )

    output_base_dir = _resolve_repo_path(settings.allowed_output_base_dir)
    try:
        output_base_dir.mkdir(parents=True, exist_ok=True)
        checks.append({"name": "output_base_dir", "status": "ok", "detail": str(output_base_dir)})
    except OSError as exc:
        checks.append({"name": "output_base_dir", "status": "failed", "detail": str(exc)})

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
        except (httpx.HTTPError, OSError) as exc:
            checks.append(
                {
                    "name": "llm_connectivity",
                    "status": "failed",
                    "detail": str(exc),
                }
            )
    else:
        checks.append({"name": "llm_connectivity", "status": "skipped", "detail": "LLM disabled"})

    checks.append(
        {
            "name": "runtime_boundary",
            "status": "ok" if runtime_boundary["pilot_ready"] else "warning",
            "detail": (
                "customer-owned single-process pilot boundary configured"
                if runtime_boundary["pilot_ready"]
                else (
                    "development/evaluation posture only; shared access requires customer ownership, "
                    "upstream rate limiting, persistent audit storage, and explicit secrets"
                )
            ),
        }
    )

    failed_checks = [check["name"] for check in checks if check.get("status") == "failed"]
    warning_checks = [check["name"] for check in checks if check.get("status") == "warning"]
    overall_status = "healthy" if not failed_checks else "degraded"

    return {
        "overall_status": overall_status,
        "failed_checks": failed_checks,
        "warning_checks": warning_checks,
        "checks": checks,
        "runtime_boundary": runtime_boundary,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _process_report_schema() -> dict[str, Any]:
    return {
        "schema": PROCESS_REPORT_SCHEMA,
        "required_sections": [
            "success",
            "outcome.metrics",
            "outcome.artifacts",
        ],
        "operator_rules": [
            "Processing input, output, and template paths must remain under configured base directories.",
            "Use signed audit exports and verification when moving artifacts across regulated workflows.",
            "Auth roles should be reviewed before opening processing endpoints to shared operators.",
        ],
    }


def _service_brief_payload() -> dict[str, Any]:
    auth_bootstrap = _auth_bootstrap_snapshot()
    readiness = _service_readiness()
    runtime_boundary = readiness["runtime_boundary"]
    allowed_roles = sorted(_allowed_process_roles())
    auth_mode = "enabled" if settings.auth_enabled else "disabled"
    signing_mode = "enabled" if settings.export_signing_enabled else "disabled"

    return {
        "status": "ok" if readiness["overall_status"] == "healthy" else "degraded",
        "service": "secure-xl2hwp-local",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "readiness_contract": SERVICE_BRIEF_CONTRACT,
        "headline": (
            "Air-gapped spreadsheet-to-document pipeline with path guardrails, signed audit exports, "
            "and operator-facing readiness checks."
        ),
        "report_contract": _process_report_schema(),
        "auth_mode": auth_mode,
        "signing_mode": signing_mode,
        "allowed_process_roles": allowed_roles,
        "bootstrap_state": auth_bootstrap,
        "readiness": readiness,
        "runtime_boundary": runtime_boundary,
        "evidence_counts": {
            "allowed_roles": len(allowed_roles),
            "readiness_failed_checks": len(readiness["failed_checks"]),
            "login_guard_max_failures": login_attempt_guard.max_failures,
            "service_routes": len(SERVICE_BRIEF_ROUTES),
        },
        "architecture_flow": [
            "Open /health to confirm auth bootstrap state, signing posture, and path boundaries.",
            "Read /ops/runtime-scorecard and /ops/service-brief before operator onboarding to confirm review flow, operating posture, and trust boundary.",
            "Inspect /ops/template-drift-preview before changing templates or exporting regulated documents.",
            "Open /ops/export-verification-pack before any export handoff that depends on signed bundles.",
            "Open /ops/offline-deployment-pack before shared workstation rollout or constrained-environment delivery.",
            "Run /ops/readiness before processing regulated spreadsheets or enabling LLM cleanup.",
            "Only then use /process/path or /process/file and archive signed audit exports for traceability.",
        ],
        "two_minute_architecture": [
            "Open /health and confirm bootstrap state, signing posture, and path guardrails.",
            "Open /ops/runtime-scorecard and confirm runtime score, audit event count, and latest process posture.",
            "Open /ops/service-brief and verify allowed roles, failed checks, and trust boundary.",
            "Open /ops/export-verification-pack and confirm signature, digest, and handoff gate posture.",
            "Open /ops/offline-deployment-pack and confirm shared-operator rollout gates.",
            "Run /ops/readiness before enabling LLM cleanup or onboarding shared operators.",
            "Approve regulated spreadsheet processing only after signed audit export routes are reachable.",
        ],
        "watchouts": [
            "This service is designed for local or air-gapped operation; cloud dependencies should remain optional.",
            "If auth bootstrap is still required, shared access should not be opened yet.",
            "The built-in login guard and audit hash state are process-local; shared access requires one app worker plus an upstream rate limiter.",
            "Signed exports improve traceability, but they do not replace input or template validation.",
        ],
        "trust_boundary": [
            "Spreadsheet files stay within configured input/output/template base directories.",
            "JWT access control and process-role restrictions gate high-impact processing endpoints.",
            "Audit summaries and signature verification surfaces exist for audit evidence, not just operator convenience.",
        ],
        "proof_assets": [
            {
                "label": "Health Envelope",
                "path": "/health",
                "why": "Shows bootstrap state, signing posture, and next operator action.",
            },
            {
                "label": "Runtime Scorecard",
                "path": "/ops/runtime-scorecard",
                "why": "Summarizes auth bootstrap, recent audit flow, and runtime readiness in one compact payload.",
            },
            {
                "label": "Service Brief",
                "path": "/ops/service-brief",
                "why": "Pins allowed roles, failed checks, trust boundary, and process contract.",
            },
            {
                "label": "Template Drift Preview",
                "path": "/ops/template-drift-preview",
                "why": "Shows placeholder drift and what needs re-review before export.",
            },
            {
                "label": "Export Verification Pack",
                "path": "/ops/export-verification-pack",
                "why": "Groups signed bundle verification, digest posture, and handoff gate proof in one route.",
            },
            {
                "label": "Offline Deployment Pack",
                "path": "/ops/offline-deployment-pack",
                "why": "Shows air-gapped rollout, workstation trust boundary, and shared-operator readiness in one payload.",
            },
            {
                "label": "Readiness Check",
                "path": "/ops/readiness",
                "why": "Provides the preflight system check before regulated processing starts.",
            },
            {
                "label": "Process Schema",
                "path": "/ops/schema/process-report",
                "why": "Locks the expected pipeline output and artifact contract for verification.",
            },
        ],
        "routes": SERVICE_BRIEF_ROUTES,
    }


def _export_verification_pack_payload() -> dict[str, Any]:
    audit_summary = _audit_summary(_recent_audit_events(limit=120))
    hash_chain_valid = bool(audit_summary.get("hash_chain_valid", False))
    total_events = int(audit_summary.get("total_events", 0))
    signing_enabled = bool(settings.export_signing_enabled)
    verification_ready = signing_enabled and hash_chain_valid

    return {
        "status": "ok" if verification_ready else "degraded",
        "service": "secure-xl2hwp-local",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema": "secure-xl2hwp-export-verification-pack-v1",
        "headline": "Signed export verification pack for regulated export handoff and tamper-evident bundle approval.",
        "summary": {
            "signing_enabled": signing_enabled,
            "hash_chain_valid": hash_chain_valid,
            "audit_event_count": total_events,
            "verification_ready": verification_ready,
        },
        "verification_contract": {
            "bundle_route": "/ops/audit/export/summary.bundle.zip",
            "verify_route": "/ops/audit/export/verify",
            "required_checks": [
                "signature bundle exists",
                "hash chain is valid",
                "independent verify endpoint passes",
            ],
        },
        "architecture_actions": [
            "Download the signed summary bundle only after the verification pack is healthy.",
            "Treat a broken hash chain as an export handoff blocker, not a warning.",
            "Keep signature verification and signed bundle export in the same walkthrough for regulated delivery.",
        ],
        "links": {
            "health": "/health",
            "runtime_scorecard": "/ops/runtime-scorecard",
            "service_brief": "/ops/service-brief",
            "architecture_pack": "/ops/architecture-pack",
            "signed_summary_bundle": "/ops/audit/export/summary.bundle.zip",
            "verify_bundle": "/ops/audit/export/verify",
            "export_verification_pack": "/ops/export-verification-pack",
        },
    }


def _offline_deployment_pack_payload() -> dict[str, Any]:
    auth_bootstrap = _auth_bootstrap_snapshot()
    readiness = _service_readiness()
    runtime_boundary = readiness["runtime_boundary"]
    failed_checks = len(readiness["failed_checks"])
    shared_operator_ready = (
        (not auth_bootstrap["required"])
        and failed_checks == 0
        and bool(runtime_boundary["pilot_ready"])
    )

    return {
        "status": "ok" if shared_operator_ready else "degraded",
        "service": "secure-xl2hwp-local",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema": "secure-xl2hwp-offline-deployment-pack-v1",
        "headline": (
            "Offline deployment pack for secure workstation rollout, signed handoff posture, "
            "and constrained-environment operation."
        ),
        "summary": {
            "deployment_mode": "air-gapped-local",
            "shared_operator_ready": shared_operator_ready,
            "auth_bootstrap_required": auth_bootstrap["required"],
            "failed_readiness_checks": failed_checks,
            "signing_enabled": settings.export_signing_enabled,
            "llm_cleanup_optional": settings.enable_llm,
            "allowed_process_roles": len(_allowed_process_roles()),
            "runtime_boundary": runtime_boundary,
        },
        "deployment_contract": {
            "runtime_target": "local or air-gapped operator workstation",
            "required_directories": {
                "input_base_dir": settings.allowed_input_base_dir,
                "output_base_dir": settings.allowed_output_base_dir,
                "template_base_dir": settings.allowed_template_base_dir,
                "audit_log_dir": settings.audit_log_dir,
            },
            "required_architecture_routes": [
                "/health",
                "/ops/service-brief",
                "/ops/runtime-scorecard",
                "/ops/export-verification-pack",
                "/ops/offline-deployment-pack",
                "/ops/readiness",
            ],
            "shared_operator_gate": {
                "auth_bootstrap_complete": not auth_bootstrap["required"],
                "readiness_passed": failed_checks == 0,
                "signed_export_enabled": settings.export_signing_enabled,
                "customer_owned_runtime": runtime_boundary["runtime_owner"] == "customer",
                "upstream_rate_limit_configured": runtime_boundary["rate_limit"][
                    "upstream_configured"
                ],
                "persistent_audit_storage": runtime_boundary["audit_state"][
                    "persistent_storage_configured"
                ],
            },
        },
        "operator_handoff": {
            "ready_for_shared_operator_rollout": shared_operator_ready,
            "blocking_reason": None
            if shared_operator_ready
            else (
                "auth bootstrap required"
                if auth_bootstrap["required"]
                else (
                    f"{failed_checks} readiness checks still failing"
                    if failed_checks
                    else "customer-owned pilot boundary is not configured"
                )
            ),
            "next_architecture_gate": (
                "Run /ops/readiness and verify /ops/export-verification-pack before shared rollout."
            ),
        },
        "architecture_actions": [
            "Keep offline rollout tied to the same signed export and audit surfaces used for export handoff.",
            "Treat auth bootstrap and readiness failures as rollout blockers for shared operators.",
            "Keep exactly one application worker until login throttling and audit hash state use a shared backend.",
            "Use this pack to document workstation trust boundaries before enabling regulated processing.",
        ],
        "links": {
            "health": "/health",
            "service_brief": "/ops/service-brief",
            "runtime_scorecard": "/ops/runtime-scorecard",
            "export_verification_pack": "/ops/export-verification-pack",
            "offline_deployment_pack": "/ops/offline-deployment-pack",
            "architecture_pack": "/ops/architecture-pack",
            "readiness": "/ops/readiness",
        },
    }


def _architecture_pack_payload() -> dict[str, Any]:
    brief = _service_brief_payload()
    auth_bootstrap = brief["bootstrap_state"]
    readiness = brief["readiness"]
    export_verification = _export_verification_pack_payload()
    offline_deployment = _offline_deployment_pack_payload()
    runtime_boundary = readiness["runtime_boundary"]
    failed_checks = len(readiness["failed_checks"])
    ready_for_handoff = (
        (not auth_bootstrap["required"])
        and failed_checks == 0
        and bool(runtime_boundary["pilot_ready"])
    )

    return {
        "status": brief["status"],
        "service": "secure-xl2hwp-local",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "readiness_contract": ARCHITECTURE_PACK_CONTRACT,
        "headline": (
            "Review brief for a local spreadsheet-to-HWP pipeline: auth bootstrap, signed export evidence, "
            "and regulated path boundaries in one surface."
        ),
        "proof_bundle": {
            "auth_bootstrap_state": "required" if auth_bootstrap["required"] else "ready",
            "signed_export_mode": brief["signing_mode"],
            "readiness_failed_checks": len(readiness["failed_checks"]),
            "allowed_process_roles": len(brief["allowed_process_roles"]),
            "audit_chain_valid": _audit_summary(_recent_audit_events(limit=120)).get("hash_chain_valid", False),
            "architecture_endpoints": [
                "/health",
                "/ops/runtime-scorecard",
                "/ops/service-brief",
                "/ops/template-drift-preview",
                "/ops/export-verification-pack",
                "/ops/offline-deployment-pack",
                "/ops/architecture-pack",
                "/ops/audit/summary",
                "/ops/audit/export/summary.bundle.zip",
                "/ops/audit/export/verify",
            ],
            "export_verification_contract": export_verification["schema"],
            "offline_deployment_contract": offline_deployment["schema"],
            "runtime_boundary": runtime_boundary,
        },
        "approval_gate": {
            "auth_bootstrap_required": auth_bootstrap["required"],
            "audit_roles_required": ["Admin", "Auditor"],
            "process_roles": brief["allowed_process_roles"],
            "signed_export_required_for_handoff": settings.export_signing_enabled,
        },
        "handoff_bundle": {
            "ready_for_handoff": ready_for_handoff,
            "signed_bundle_path": "/ops/audit/export/summary.bundle.zip",
            "verify_route": "/ops/audit/export/verify",
            "blocking_reason": None
            if ready_for_handoff
            else (
                "auth bootstrap required"
                if auth_bootstrap["required"]
                else (
                    f"{failed_checks} readiness checks still failing"
                    if failed_checks
                    else "customer-owned pilot boundary is not configured"
                )
            ),
        },
        "target_boundary": {
            "input_base_dir": settings.allowed_input_base_dir,
            "output_base_dir": settings.allowed_output_base_dir,
            "template_base_dir": settings.allowed_template_base_dir,
            "audit_log_dir": settings.audit_log_dir,
        },
        "artifacts": [
            "Signed summary bundle export for export handoff.",
            "Signed recent-audit bundle export for regulated evidence trails.",
            "Signature verification endpoint for independent bundle verification.",
            "Offline deployment pack for workstation rollout and shared-operator readiness.",
        ],
        "architecture_sequence": [
            "Open /health, /ops/runtime-scorecard, and /ops/service-brief to confirm bootstrap state, role posture, signing mode, and recent audit health.",
            "Run /ops/readiness before enabling LLM cleanup or onboarding shared operators.",
            "Inspect /ops/export-verification-pack before trusting signed bundle delivery posture.",
            "Inspect /ops/offline-deployment-pack before enabling shared workstation rollout or cross-team handoff.",
            "Inspect /ops/audit/summary and the signed export bundles together so the export handoff reads like evidence, not just logs.",
            "Verify exported bundle integrity with /ops/audit/export/verify before moving across trust boundaries.",
        ],
        "two_minute_architecture": [
            "Open /health, /ops/runtime-scorecard, /ops/service-brief, and /ops/architecture-pack to confirm bootstrap state and signing posture.",
            "Open /ops/export-verification-pack before approving any signed verification bundle.",
            "Open /ops/offline-deployment-pack before approving shared workstation rollout.",
            "Run /ops/readiness and inspect failed checks before processing regulated spreadsheets.",
            "Review signed summary or audit bundles before downstream delivery approval.",
            "Verify the exported bundle with /ops/audit/export/verify before crossing trust boundaries.",
        ],
        "watchouts": [
            "Signed bundles provide tamper evidence, but they do not validate spreadsheet semantics automatically.",
            "If auth bootstrap is still required, the workstation is not ready for shared operator access.",
            "Process-local throttling and audit state do not support multiple application workers.",
            "Path guardrails are only effective when base directories remain locked down in deployment.",
        ],
        "proof_assets": [
            {
                "label": "Runtime Scorecard",
                "path": "/ops/runtime-scorecard",
                "why": "Compresses audit flow, auth bootstrap, and runtime posture before downstream approval.",
            },
            {
                "label": "Service Brief",
                "path": "/ops/service-brief",
                "why": "Summarizes roles, readiness posture, and trust boundary before processing.",
            },
            {
                "label": "Review Pack",
                "path": "/ops/architecture-pack",
                "why": "Packages approval gate, boundary, artifacts, and review sequence in one payload.",
            },
            {
                "label": "Export Verification Pack",
                "path": "/ops/export-verification-pack",
                "why": "Makes signed bundle verification and handoff readiness explicit before regulated delivery.",
            },
            {
                "label": "Offline Deployment Pack",
                "path": "/ops/offline-deployment-pack",
                "why": "Documents workstation rollout, shared-operator gates, and air-gapped deployment posture.",
            },
            {
                "label": "Signed Summary Bundle",
                "path": "/ops/audit/export/summary.bundle.zip",
                "why": "Provides export-ready evidence with payload plus signature manifest.",
            },
            {
                "label": "Verify Bundle",
                "path": "/ops/audit/export/verify",
                "why": "Lets a user independently validate the bundle before handoff.",
            },
        ],
        "links": {
            "health": "/health",
            "runtime_scorecard": "/ops/runtime-scorecard",
            "service_brief": "/ops/service-brief",
            "architecture_pack": "/ops/architecture-pack",
            "export_verification_pack": "/ops/export-verification-pack",
            "offline_deployment_pack": "/ops/offline-deployment-pack",
            "template_drift_preview": "/ops/template-drift-preview",
            "readiness": "/ops/readiness",
            "audit_summary": "/ops/audit/summary",
            "signed_summary_bundle": "/ops/audit/export/summary.bundle.zip",
            "verify_bundle": "/ops/audit/export/verify",
        },
    }


def _runtime_scorecard_payload() -> dict[str, Any]:
    brief = _service_brief_payload()
    audit_events = _recent_audit_events(limit=120)
    audit_summary = _audit_summary(audit_events)
    readiness = brief["readiness"]
    failed_checks = int(len(readiness.get("failed_checks", [])))
    auth_bootstrap_required = bool(brief["bootstrap_state"]["required"])
    runtime_boundary = brief["runtime_boundary"]
    process_success_rate = audit_summary.get("process_success_rate")
    success_rate_value = float(process_success_rate) if process_success_rate is not None else 100.0
    runtime_score = max(
        40,
        100
        - min(failed_checks * 12, 40)
        - (15 if auth_bootstrap_required else 0)
        - (15 if not runtime_boundary["pilot_ready"] else 0)
        - (10 if success_rate_value < 95 else 0),
    )
    top_actor = (audit_summary.get("top_actors") or [{}])[0]
    latest_process = (audit_summary.get("process_timeline") or [{}])[-1]
    return {
        "status": brief["status"],
        "service": "secure-xl2hwp-local",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "readiness_contract": RUNTIME_SCORECARD_CONTRACT,
        "headline": "Compact runtime scorecard for auth bootstrap, signed export posture, and recent audit flow.",
        "summary": {
            "runtime_score": runtime_score,
            "auth_mode": brief["auth_mode"],
            "signing_mode": brief["signing_mode"],
            "readiness_failed_checks": failed_checks,
            "audit_event_count": audit_summary.get("total_events", 0),
            "audit_chain_valid": audit_summary.get("hash_chain_valid", False),
            "process_success_rate": process_success_rate,
            "auth_bootstrap_required": auth_bootstrap_required,
            "pilot_boundary_configured": runtime_boundary["pilot_ready"],
            "production_ready": False,
        },
        "runtime": {
            "allowed_process_roles": brief["allowed_process_roles"],
            "login_guard_max_failures": login_attempt_guard.max_failures,
            "readiness_overall_status": readiness["overall_status"],
            "audit_log_dir": settings.audit_log_dir,
            "boundary": runtime_boundary,
        },
        "audit_snapshot": {
            "top_actor": top_actor,
            "latest_process": latest_process,
            "process_status_counts": audit_summary.get("process_status_counts", {}),
            "hash_chain": {
                "valid": audit_summary.get("hash_chain_valid", False),
                "checked": audit_summary.get("hash_chain_checked", 0),
                "broken": audit_summary.get("hash_chain_broken", 0),
            },
        },
        "fastest_architecture_path": [
            "/health",
            "/ops/runtime-scorecard",
            "/ops/service-brief",
            "/ops/template-drift-preview",
            "/ops/export-verification-pack",
            "/ops/offline-deployment-pack",
            "/ops/readiness",
            "/ops/audit/summary",
        ],
        "links": {
            "health": "/health",
            "runtime_scorecard": "/ops/runtime-scorecard",
            "service_brief": "/ops/service-brief",
            "template_drift_preview": "/ops/template-drift-preview",
            "export_verification_pack": "/ops/export-verification-pack",
            "offline_deployment_pack": "/ops/offline-deployment-pack",
            "architecture_pack": "/ops/architecture-pack",
            "readiness": "/ops/readiness",
            "audit_summary": "/ops/audit/summary",
        },
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
    auth_bootstrap = _auth_bootstrap_snapshot()
    default_input_path = str(Path(settings.allowed_input_base_dir) / "sample_projects.xlsx")
    default_template_path = str(Path(settings.allowed_template_base_dir) / "sample_report_template.txt")
    ui_config = {
        "auth_enabled": settings.auth_enabled,
        "auth_bootstrap": auth_bootstrap,
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
            "input_path": default_input_path,
            "output_dir": settings.allowed_output_base_dir,
            "contract_name": "default",
            "profile_name": "default",
            "template_name": "default",
            "template_path": default_template_path,
        },
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"ui_config_json": json.dumps(ui_config, ensure_ascii=False)},
    )


@app.get("/health")
def health() -> dict:
    auth_bootstrap = _auth_bootstrap_snapshot()
    runtime_boundary = settings.runtime_boundary()
    diagnostics = {
        "auth_mode": "enabled" if settings.auth_enabled else "disabled",
        "bootstrap_state": "required" if auth_bootstrap["required"] else "ready",
        "llm_mode": "enabled" if settings.enable_llm else "disabled",
        "export_signing_mode": "enabled" if settings.export_signing_enabled else "disabled",
        "next_action": (
            "Create the initial admin bootstrap record before opening shared access."
            if auth_bootstrap["required"]
            else (
                "Configure the customer-owned pilot boundary before opening shared access."
                if not runtime_boundary["pilot_ready"]
                else (
                    "Verify Ollama reachability from /ops/readiness before running LLM cleanup."
                    if settings.enable_llm
                    else "Review /ops/architecture-pack and run /ops/readiness before processing regulated spreadsheets."
                )
            )
        ),
    }
    return {
        "status": "ok",
        "service": "secure-xl2hwp-local",
        "readiness_contract": SERVICE_BRIEF_CONTRACT,
        "report_contract": _process_report_schema(),
        "app": settings.app_name,
        "env": settings.app_env,
        "llm_enabled": settings.enable_llm,
        "auth_enabled": settings.auth_enabled,
        "auth_bootstrap_required": auth_bootstrap["required"],
        "auth_bootstrap": auth_bootstrap,
        "auth_login_guard": {
            "max_failures": login_attempt_guard.max_failures,
            "window_seconds": login_attempt_guard.window_seconds,
            "lock_seconds": login_attempt_guard.lock_seconds,
            "scope": "process-local",
            "resets_on_restart": True,
        },
        "runtime_boundary": runtime_boundary,
        "process_allowed_roles": sorted(_allowed_process_roles()),
        "allowed_input_base_dir": settings.allowed_input_base_dir,
        "allowed_output_base_dir": settings.allowed_output_base_dir,
        "allowed_template_base_dir": settings.allowed_template_base_dir,
        "audit_log_dir": settings.audit_log_dir,
        "export_signing_enabled": settings.export_signing_enabled,
        "export_signing_key_id": settings.export_signing_key_id if settings.export_signing_enabled else None,
        "diagnostics": diagnostics,
        "ops_contract": {
            "schema": "ops-envelope-v1",
            "version": 1,
            "required_fields": ["service", "status", "diagnostics.next_action"],
        },
        "capabilities": [
            "local-excel-processing",
            "signed-audit-export",
            "role-based-ops-console",
            "llm-assisted-cleanup",
            "service-brief-surface",
            "runtime-scorecard-surface",
            "template-drift-preview-surface",
            "export-verification-pack-surface",
            "offline-deployment-pack-surface",
            "process-report-schema",
            "architecture-pack-surface",
        ],
        "routes": SERVICE_BRIEF_ROUTES,
        "links": {
            "readiness": "/ops/readiness",
            "service_brief": "/ops/service-brief",
            "runtime_scorecard": "/ops/runtime-scorecard",
            "template_drift_preview": "/ops/template-drift-preview",
            "export_verification_pack": "/ops/export-verification-pack",
            "offline_deployment_pack": "/ops/offline-deployment-pack",
            "architecture_pack": "/ops/architecture-pack",
            "process_schema": "/ops/schema/process-report",
            "login": "/auth/login",
            "audit_summary": "/ops/audit/summary",
            "process_file": "/process/file",
        },
    }


@app.get("/ops/service-brief")
def service_brief() -> dict[str, Any]:
    return _service_brief_payload()


@app.get("/ops/runtime-scorecard")
def runtime_scorecard() -> dict[str, Any]:
    return _runtime_scorecard_payload()


@app.get("/ops/template-drift-preview")
def template_drift_preview() -> dict[str, Any]:
    return _template_drift_preview_payload()


@app.get("/ops/export-verification-pack")
def export_verification_pack() -> dict[str, Any]:
    return _export_verification_pack_payload()


@app.get("/ops/offline-deployment-pack")
def offline_deployment_pack() -> dict[str, Any]:
    return _offline_deployment_pack_payload()


@app.get("/ops/architecture-pack")
def architecture_pack() -> dict[str, Any]:
    return _architecture_pack_payload()


@app.get("/ops/schema/process-report")
def process_report_schema() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "secure-xl2hwp-local",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        **_process_report_schema(),
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
        "scope": "process-local",
        "resets_on_restart": True,
        "cross_process_safe": False,
        "upstream_required_for_shared_access": True,
        "upstream_configured": settings.auth_rate_limit_mode == "upstream-enforced",
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
        safe_input_path, safe_output_dir, safe_template_path = _validate_process_path_request(
            input_path=req.input_path,
            output_dir=req.output_dir,
            template_path=req.template_path,
        )
        outcome = service.process(
            input_path=safe_input_path,
            output_dir=safe_output_dir,
            contract_name=req.contract_name,
            profile_name=req.profile_name,
            template_name=req.template_name,
            template_path=safe_template_path,
            actor=_actor(current_user),
            request_id=request.state.request_id,
        )
    except (ValueError, OSError, KeyError, TypeError, HTTPException) as exc:
        _raise_mapped_http_error(exc, request)

    return ProcessResponse(success=True, outcome=outcome.to_dict())


@app.post("/process/file", response_model=ProcessResponse)
async def process_upload(
    request: Request,
    file: UploadFile = File(...),
    output_dir: str = Form("examples/output"),
    contract_name: str = Form("default"),
    profile_name: str = Form("default"),
    template_name: str = Form("default"),
    template_path: str = Form(""),
    current_user: AuthUser = Depends(require_process_user),
) -> ProcessResponse:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")

    service = PipelineService(settings=settings, audit_logger=audit_logger)
    temp_path = ""

    try:
        max_bytes = settings.max_upload_mb * 1024 * 1024
        total_bytes = 0
        safe_output_dir, safe_template_path = _validate_upload_request_paths(
            output_dir=output_dir,
            template_path=template_path or None,
        )
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
            output_dir=safe_output_dir,
            contract_name=contract_name,
            profile_name=profile_name,
            template_name=template_name,
            template_path=safe_template_path,
            actor=_actor(current_user),
            request_id=request.state.request_id,
        )
    except (ValueError, OSError, KeyError, TypeError, HTTPException) as exc:
        _raise_mapped_http_error(exc, request)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    return ProcessResponse(success=True, outcome=outcome.to_dict())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=False)
