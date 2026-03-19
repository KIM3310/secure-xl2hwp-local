from __future__ import annotations

import hashlib
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _stable_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def _compute_event_hash(prev_hash: str, payload: dict[str, Any]) -> str:
    material = f"{prev_hash}|{_stable_json(payload)}".encode()
    return hashlib.sha256(material).hexdigest()


class AuditLogger:
    def __init__(self, audit_log_dir: str = "logs/audit") -> None:
        self.audit_log_dir = Path(audit_log_dir)
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _read_prev_hash(self, path: Path) -> str:
        if not path.exists():
            return "GENESIS"

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return "GENESIS"

        for raw_line in reversed(lines):
            line = raw_line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                return "GENESIS"
            event_hash = str(parsed.get("event_hash", "")).strip()
            return event_hash or "GENESIS"

        return "GENESIS"

    def log_event(
        self,
        event_type: str,
        status: str,
        actor: Optional[dict[str, str]] = None,
        request_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp_utc": now.isoformat(),
            "event_type": event_type,
            "status": status,
            "request_id": request_id,
            "actor": actor or {"user_id": "unknown", "role": "unknown"},
            "details": details or {},
        }

        file_name = f"{now.strftime('%Y-%m-%d')}.jsonl"
        path = self.audit_log_dir / file_name

        try:
            with self._lock:
                prev_hash = self._read_prev_hash(path)
                payload = {**event, "prev_hash": prev_hash}
                payload["event_hash"] = _compute_event_hash(prev_hash, payload)
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload, ensure_ascii=False, default=str))
                    handle.write("\n")
        except OSError as exc:
            logger.warning("Failed to write audit event: %s", exc)

        return payload if "payload" in locals() else event
