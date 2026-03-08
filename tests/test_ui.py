import hashlib
import hmac
import io
import json
import zipfile

from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import app

client = TestClient(app)


def test_ui_home_page() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Secure XL2HWP Studio" in response.text
    assert "LOCAL SECURE AUTOMATION" in response.text
    assert "langSelect" in response.text
    assert "themeSelect" in response.text
    assert "brandSelect" in response.text
    assert "statusChartCanvas" in response.text
    assert "opsEventTypeSelect" in response.text
    assert "opsActorInput" in response.text
    assert "exportSummaryBtn" in response.text
    assert "exportAuditCsvBtn" in response.text
    assert "verifyForm" in response.text
    assert "verifyPayloadFile" in response.text
    assert "verifySignatureFile" in response.text
    assert "refreshReadinessBtn" in response.text
    assert "readinessList" in response.text
    assert "bootstrapCard" in response.text
    assert "bootstrapHashCommand" in response.text
    assert "bootstrapYamlTemplate" in response.text
    assert "briefHeadline" in response.text
    assert "briefSchema" in response.text
    assert "briefReviewFlow" in response.text
    assert "briefTrustBoundary" in response.text
    assert "reviewPackHeadline" in response.text
    assert "reviewPackSequence" in response.text


def test_health_includes_auth_bootstrap_state() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "secure-xl2hwp-local"
    assert "auth_bootstrap_required" in payload
    assert "auth_bootstrap" in payload
    assert "diagnostics" in payload
    assert payload["links"]["readiness"] == "/ops/readiness"
    assert "signed-audit-export" in payload["capabilities"]
    bootstrap = payload["auth_bootstrap"]
    assert "required" in bootstrap
    assert "total_users" in bootstrap
    assert "active_users" in bootstrap
    assert "registry_path" in bootstrap
    assert bootstrap["registry_path"].endswith(".yaml")
    assert payload["diagnostics"]["bootstrap_state"] in {"required", "ready"}
    assert "next_action" in payload["diagnostics"]
    assert payload["ops_contract"]["schema"] == "ops-envelope-v1"
    assert payload["readiness_contract"] == "secure-xl2hwp-service-brief-v1"
    assert payload["report_contract"]["schema"] == "secure-xl2hwp-process-report-v1"
    assert payload["links"]["service_brief"] == "/ops/service-brief"
    assert payload["links"]["review_pack"] == "/ops/review-pack"
    assert payload["links"]["process_schema"] == "/ops/schema/process-report"
    assert "/ops/service-brief" in payload["routes"]
    assert "/ops/review-pack" in payload["routes"]
    assert "service-brief-surface" in payload["capabilities"]
    assert "review-pack-surface" in payload["capabilities"]


def test_service_brief_and_process_schema_shape() -> None:
    brief_response = client.get("/ops/service-brief")
    assert brief_response.status_code == 200
    brief_payload = brief_response.json()
    assert brief_payload["readiness_contract"] == "secure-xl2hwp-service-brief-v1"
    assert brief_payload["report_contract"]["schema"] == "secure-xl2hwp-process-report-v1"
    assert isinstance(brief_payload["review_flow"], list)
    assert isinstance(brief_payload["trust_boundary"], list)
    assert len(brief_payload["two_minute_review"]) == 4
    assert brief_payload["proof_assets"][0]["path"] == "/health"
    assert "/process/file" in brief_payload["routes"]

    review_response = client.get("/ops/review-pack")
    assert review_response.status_code == 200
    review_payload = review_response.json()
    assert review_payload["readiness_contract"] == "secure-xl2hwp-review-pack-v1"
    assert review_payload["links"]["verify_bundle"] == "/ops/audit/export/verify"
    assert "/ops/review-pack" in review_payload["proof_bundle"]["review_endpoints"]
    assert isinstance(review_payload["review_sequence"], list)
    assert len(review_payload["two_minute_review"]) == 4
    assert review_payload["proof_assets"][0]["label"] == "Service Brief"

    schema_response = client.get("/ops/schema/process-report")
    assert schema_response.status_code == 200
    schema_payload = schema_response.json()
    assert schema_payload["schema"] == "secure-xl2hwp-process-report-v1"
    assert "outcome.metrics" in schema_payload["required_sections"]


def test_audit_recent_requires_audit_role() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-analyst", "password": "analyst123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        "/ops/audit/recent?limit=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_audit_recent_with_admin_role() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        "/ops/audit/recent?limit=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "count" in payload
    assert "events" in payload
    assert isinstance(payload["events"], list)


def test_audit_summary_requires_audit_role() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-analyst", "password": "analyst123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        "/ops/audit/summary?limit=40",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_audit_summary_with_admin_role() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        "/ops/audit/summary?limit=40",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "count" in payload
    assert "summary" in payload
    assert "anomalies" in payload
    assert "applied_filters" in payload
    assert "process_status_counts" in payload["summary"]
    assert "process_hourly" in payload["summary"]


def test_audit_summary_filter_returns_zero_for_unknown_status() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/ops/audit/summary?limit=80&status=definitely_unknown",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 0
    assert payload["applied_filters"]["status"] == "definitely_unknown"


def test_audit_recent_filter_shape() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/ops/audit/recent?limit=10&since_hours=24&status=succeeded&event_type=pipeline.process&actor_contains=demo",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "count" in payload
    assert "events" in payload
    assert "applied_filters" in payload
    assert payload["applied_filters"]["since_hours"] == 24
    assert payload["applied_filters"]["event_type"] == "pipeline.process"
    assert payload["applied_filters"]["actor_contains"] == "demo"


def test_audit_export_summary_contains_signature_headers() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/ops/audit/export/summary?limit=60&since_hours=24",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "x-export-sha256" in response.headers
    assert "x-export-signature" in response.headers
    assert response.headers["x-export-signature-alg"] in {"hmac-sha256", "none"}

    sha = hashlib.sha256(response.content).hexdigest()
    assert response.headers["x-export-sha256"] == sha

    settings = get_settings()
    if settings.export_signing_enabled:
        expected_sig = hmac.new(
            settings.export_signing_key.encode("utf-8"),
            response.content,
            hashlib.sha256,
        ).hexdigest()
        assert response.headers["x-export-signature"] == expected_sig


def test_ops_readiness_requires_audit_role() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-analyst", "password": "analyst123!"},
    )
    token = login_response.json()["access_token"]
    response = client.get(
        "/ops/readiness",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_ops_readiness_with_admin_role_shape() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]
    response = client.get(
        "/ops/readiness",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] in {"healthy", "degraded"}
    assert isinstance(payload["checks"], list)
    check_names = {row["name"] for row in payload["checks"]}
    assert {"specs", "audit_log_dir", "export_signing", "llm_connectivity"}.issubset(check_names)


def test_audit_export_summary_bundle_zip_contains_payload_and_signature() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]
    response = client.get(
        "/ops/audit/export/summary.bundle.zip?limit=60",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    assert "x-bundle-sha256" in response.headers

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = archive.namelist()
        assert any(name.endswith(".sig.json") for name in names)
        assert any(name.endswith(".json") and not name.endswith(".sig.json") for name in names)
        sig_name = next(name for name in names if name.endswith(".sig.json"))
        sig_payload = json.loads(archive.read(sig_name).decode("utf-8"))
        assert "signature" in sig_payload
        assert "sha256" in sig_payload["signature"]


def test_audit_export_recent_bundle_zip_contains_payload_and_signature() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]
    response = client.get(
        "/ops/audit/export/recent.bundle.zip?limit=50&event_type=pipeline.process",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    assert "x-bundle-sha256" in response.headers

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = archive.namelist()
        csv_name = next(name for name in names if name.endswith(".csv"))
        csv_text = archive.read(csv_name).decode("utf-8")
        assert "timestamp_utc,event_type,status,actor_user_id,actor_role" in csv_text
        assert any(name.endswith(".sig.json") for name in names)


def test_audit_export_csv_contains_signature_headers_and_csv_format() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/ops/audit/export/recent.csv?limit=50&event_type=pipeline.process",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "x-export-sha256" in response.headers
    assert "x-export-signature" in response.headers
    assert "timestamp_utc,event_type,status,actor_user_id,actor_role" in response.text


def test_audit_export_verify_accepts_valid_signed_payload() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exported = client.get("/ops/audit/export/summary?limit=40", headers=headers)
    assert exported.status_code == 200

    manifest = {
        "payload_file": "audit-summary.json",
        "signature": {
            "algorithm": exported.headers.get("x-export-signature-alg"),
            "key_id": exported.headers.get("x-export-signature-key-id"),
            "sha256": exported.headers.get("x-export-sha256"),
            "value": exported.headers.get("x-export-signature"),
        },
    }

    verify_response = client.post(
        "/ops/audit/export/verify",
        files={
            "payload_file": ("audit-summary.json", exported.content, "application/json"),
            "signature_file": ("audit-summary.sig.json", json.dumps(manifest), "application/json"),
        },
        headers=headers,
    )
    assert verify_response.status_code == 200
    payload = verify_response.json()
    assert payload["overall_valid"] is True
    assert payload["failed_checks"] == []


def test_audit_export_verify_detects_tampered_payload() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exported = client.get("/ops/audit/export/recent.csv?limit=30", headers=headers)
    assert exported.status_code == 200

    manifest = {
        "payload_file": "audit-recent.csv",
        "signature": {
            "algorithm": exported.headers.get("x-export-signature-alg"),
            "key_id": exported.headers.get("x-export-signature-key-id"),
            "sha256": exported.headers.get("x-export-sha256"),
            "value": exported.headers.get("x-export-signature"),
        },
    }
    tampered_payload = exported.content + b"\n#tampered"

    verify_response = client.post(
        "/ops/audit/export/verify",
        files={
            "payload_file": ("audit-recent.csv", tampered_payload, "text/csv"),
            "signature_file": ("audit-recent.sig.json", json.dumps(manifest), "application/json"),
        },
        headers=headers,
    )
    assert verify_response.status_code == 200
    payload = verify_response.json()
    assert payload["overall_valid"] is False
    assert "hash_match" in payload["failed_checks"]


def test_audit_export_endpoints_require_audit_role() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-analyst", "password": "analyst123!"},
    )
    token = login_response.json()["access_token"]

    summary_response = client.get(
        "/ops/audit/export/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    csv_response = client.get(
        "/ops/audit/export/recent.csv",
        headers={"Authorization": f"Bearer {token}"},
    )
    summary_bundle_response = client.get(
        "/ops/audit/export/summary.bundle.zip",
        headers={"Authorization": f"Bearer {token}"},
    )
    recent_bundle_response = client.get(
        "/ops/audit/export/recent.bundle.zip",
        headers={"Authorization": f"Bearer {token}"},
    )
    readiness_response = client.get(
        "/ops/readiness",
        headers={"Authorization": f"Bearer {token}"},
    )
    verify_response = client.post(
        "/ops/audit/export/verify",
        files={
            "payload_file": ("audit.csv", b"col\n1", "text/csv"),
            "signature_file": (
                "audit.sig.json",
                json.dumps(
                    {
                        "payload_file": "audit.csv",
                        "signature": {
                            "algorithm": "none",
                            "key_id": "none",
                            "sha256": hashlib.sha256(b"col\n1").hexdigest(),
                            "value": "",
                        },
                    }
                ),
                "application/json",
            ),
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert summary_response.status_code == 403
    assert csv_response.status_code == 403
    assert summary_bundle_response.status_code == 403
    assert recent_bundle_response.status_code == 403
    assert readiness_response.status_code == 403
    assert verify_response.status_code == 403
