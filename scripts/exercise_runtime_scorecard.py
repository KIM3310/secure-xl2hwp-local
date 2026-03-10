from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from app.main import app

    with TestClient(app) as client:
        client.get("/health").raise_for_status()
        client.get("/ops/service-brief").raise_for_status()
        scorecard = client.get("/ops/runtime-scorecard")
        scorecard.raise_for_status()
        body = scorecard.json()

    print(
        json.dumps(
            {
                "contract": body["readiness_contract"],
                "summary": body["summary"],
                "audit_snapshot": body["audit_snapshot"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
