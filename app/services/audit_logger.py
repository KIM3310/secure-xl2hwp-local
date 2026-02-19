from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    def __init__(self, audit_log_dir: str = "logs/audit") -> None:
        self.audit_log_dir = Path(audit_log_dir)
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

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
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event, ensure_ascii=False, default=str))
                    handle.write("\n")
        except Exception as exc:
            logger.warning("Failed to write audit event: %s", exc)

        return event
