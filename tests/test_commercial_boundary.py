from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_service_offer_matches_customer_owned_secure_workflow_pilot() -> None:
    docs_offer = json.loads((ROOT / "docs/service-offer.json").read_text(encoding="utf-8"))
    site_offer = json.loads((ROOT / "site/service-offer.json").read_text(encoding="utf-8"))

    assert docs_offer == site_offer
    assert docs_offer["commerce"]["lane_id"] == "secure-workflow-pilot"
    assert docs_offer["delivery_boundary"] == {
        "runtime_owner": "customer",
        "supported_topology": "single-process",
        "shared_access_requires": "upstream rate limiting and customer identity controls",
        "state": "customer-persistent filesystem; no vendor-hosted document storage",
    }
    assert docs_offer["production_exclusions"]
    assert docs_offer["pilot_deliverables"]
    assert "#private-inquiry" in docs_offer["lead_capture_url"]


def test_compose_requires_operator_secrets_and_persists_audit_state() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "JWT_SECRET_KEY: ${JWT_SECRET_KEY:?" in compose
    assert "AUTH_PASSWORD_PEPPER: ${AUTH_PASSWORD_PEPPER:?" in compose
    assert "EXPORT_SIGNING_KEY: ${EXPORT_SIGNING_KEY:?" in compose
    assert "AUTH_RATE_LIMIT_MODE: upstream-enforced" in compose
    assert "AUDIT_STORAGE_MODE: persistent-filesystem" in compose
    assert "./logs:/app/logs" in compose
