from __future__ import annotations

import json

from scripts.exercise_runtime_scorecard import (
    build_runtime_proof_snapshot,
    collect_runtime_proof,
    render_runtime_proof_snapshot,
)


def test_runtime_proof_snapshot_shape() -> None:
    payloads = collect_runtime_proof()
    snapshot = build_runtime_proof_snapshot(payloads)

    assert snapshot["contract"] == "secure-xl2hwp-runtime-scorecard-v1"
    assert snapshot["contracts"]["service_brief"] == "secure-xl2hwp-service-brief-v1"
    assert snapshot["contracts"]["export_verification_pack"] == "secure-xl2hwp-export-verification-pack-v1"
    assert snapshot["contracts"]["review_pack"] == "secure-xl2hwp-review-pack-v1"
    assert snapshot["links"]["review_pack"] == "/ops/review-pack"
    assert "/ops/review-pack" in snapshot["review_endpoints"]
    assert "/ops/export-verification-pack" in snapshot["review_endpoints"]
    assert any(asset["path"] == "/health" for asset in snapshot["proof_assets"])
    assert any(asset["path"] == "/ops/export-verification-pack" for asset in snapshot["proof_assets"])
    assert any(asset["path"] == "/ops/readiness" for asset in snapshot["proof_assets"])
    assert "required" in snapshot["auth_bootstrap"]
    assert "hash_chain" in snapshot["audit_snapshot"]


def test_runtime_proof_snapshot_can_include_full_payloads() -> None:
    payloads = collect_runtime_proof()
    snapshot = build_runtime_proof_snapshot(payloads, include_full=True)
    rendered = render_runtime_proof_snapshot(snapshot)
    parsed = json.loads(rendered)

    assert "payloads" in parsed
    assert parsed["payloads"]["health"]["service"] == "secure-xl2hwp-local"
    assert parsed["payloads"]["review_pack"]["links"]["verify_bundle"] == "/ops/audit/export/verify"
