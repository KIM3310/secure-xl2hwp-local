from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exercise_runtime_scorecard",
        description="Collect a local proof snapshot from health and ops surfaces.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include full endpoint payloads in the output for verification handoff.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path to write the JSON snapshot.",
    )
    return parser


def _quiet_noisy_loggers() -> None:
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)


def _get_json(client: TestClient, path: str) -> dict[str, Any]:
    response = client.get(path)
    response.raise_for_status()
    return response.json()


def collect_runtime_proof() -> dict[str, dict[str, Any]]:
    from app.main import app

    _quiet_noisy_loggers()

    with TestClient(app) as client:
        return {
            "health": _get_json(client, "/health"),
            "service_brief": _get_json(client, "/ops/service-brief"),
            "runtime_scorecard": _get_json(client, "/ops/runtime-scorecard"),
            "export_verification_pack": _get_json(client, "/ops/export-verification-pack"),
            "review_pack": _get_json(client, "/ops/review-pack"),
        }


def build_runtime_proof_snapshot(
    payloads: dict[str, dict[str, Any]],
    *,
    include_full: bool = False,
) -> dict[str, Any]:
    health = payloads["health"]
    brief = payloads["service_brief"]
    scorecard = payloads["runtime_scorecard"]
    export_verification_pack = payloads["export_verification_pack"]
    review_pack = payloads["review_pack"]

    snapshot: dict[str, Any] = {
        "contract": scorecard["readiness_contract"],
        "summary": scorecard["summary"],
        "audit_snapshot": scorecard["audit_snapshot"],
        "auth_bootstrap": health["auth_bootstrap"],
        "contracts": {
            "ops": health["ops_contract"]["schema"],
            "process_report": health["report_contract"]["schema"],
            "service_brief": brief["readiness_contract"],
            "runtime_scorecard": scorecard["readiness_contract"],
            "export_verification_pack": export_verification_pack["schema"],
            "review_pack": review_pack["readiness_contract"],
        },
        "proof_assets": [
            {"label": item["label"], "path": item["path"]} for item in brief["proof_assets"]
        ],
        "review_endpoints": review_pack["proof_bundle"]["review_endpoints"],
        "links": {
            "health": "/health",
            **scorecard["links"],
        },
    }
    if include_full:
        snapshot["payloads"] = payloads
    return snapshot


def render_runtime_proof_snapshot(snapshot: dict[str, Any], output_path: Path | None = None) -> str:
    rendered = json.dumps(snapshot, ensure_ascii=False, indent=2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"{rendered}\n", encoding="utf-8")
    return rendered


def main() -> None:
    args = build_parser().parse_args()
    payloads = collect_runtime_proof()
    snapshot = build_runtime_proof_snapshot(payloads, include_full=args.full)
    print(render_runtime_proof_snapshot(snapshot, args.output))


if __name__ == "__main__":
    main()
