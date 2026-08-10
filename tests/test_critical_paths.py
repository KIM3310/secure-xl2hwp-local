"""Tests for critical paths: JWT auth, login guard, export signing, pipeline stages, path guardrails."""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pandas as pd
import pytest

from app.core.settings import Settings
from app.main import (
    LoginAttemptGuard,
    _assert_path_within_base,
    _export_signature_headers,
    _resolve_repo_path,
    _validate_process_path_request,
    _validate_upload_request_paths,
    settings,
)
from app.pipeline.cot_engine import CotOrchestrator, CotResult
from app.services.auth_service import AuthService, AuthUser
from app.services.speckit_loader import SpecKitLoader
from app.services.speckit_models import CleanupProfile, DataContract

# ---------------------------------------------------------------------------
# JWT Auth Flow
# ---------------------------------------------------------------------------


class TestJwtAuthFlow:
    """Tests for JWT token issuance, verification, and edge cases."""

    @pytest.fixture()
    def auth(self):
        s = Settings(
            auth_enabled=True,
            user_registry_name="users_test",
            auth_password_pepper="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            jwt_secret_key="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
        loader = SpecKitLoader(base_path=Path("specs"))
        return AuthService(settings=s, spec_loader=loader)

    def test_issue_and_verify_roundtrip(self, auth: AuthService) -> None:
        user = AuthUser(user_id="demo-admin", role="Admin")
        token, expires_at = auth.issue_access_token(user)
        assert isinstance(token, str)
        assert len(token) > 0
        verified = auth.verify_token(token)
        assert verified.user_id == "demo-admin"
        assert verified.role == "Admin"

    def test_expired_token_raises(self, auth: AuthService) -> None:
        user = AuthUser(user_id="demo-admin", role="Admin")
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.user_id,
            "role": user.role,
            "iat": int((now - timedelta(hours=3)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
            "jti": "expired-jti",
        }
        token = jwt.encode(payload, auth.settings.jwt_secret_key, algorithm=auth.settings.jwt_algorithm)
        with pytest.raises(jwt.ExpiredSignatureError):
            auth.verify_token(token)

    def test_token_missing_sub_claim_raises(self, auth: AuthService) -> None:
        now = datetime.now(timezone.utc)
        payload = {
            "role": "Admin",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(payload, auth.settings.jwt_secret_key, algorithm=auth.settings.jwt_algorithm)
        with pytest.raises(jwt.InvalidTokenError, match="Missing token claims"):
            auth.verify_token(token)

    def test_token_missing_role_claim_raises(self, auth: AuthService) -> None:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "demo-admin",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(payload, auth.settings.jwt_secret_key, algorithm=auth.settings.jwt_algorithm)
        with pytest.raises(jwt.InvalidTokenError, match="Missing token claims"):
            auth.verify_token(token)

    def test_token_wrong_secret_raises(self, auth: AuthService) -> None:
        user = AuthUser(user_id="demo-admin", role="Admin")
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.user_id,
            "role": user.role,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "jti": "wrong-secret",
        }
        token = jwt.encode(payload, "completely-wrong-secret-key-at-least-32-chars", algorithm="HS256")
        with pytest.raises(jwt.InvalidSignatureError):
            auth.verify_token(token)

    def test_token_role_mismatch_raises(self, auth: AuthService) -> None:
        """Token role differs from what the user registry says."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "demo-admin",
            "role": "Analyst",  # actual role in registry is Admin
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "jti": "role-mismatch",
        }
        token = jwt.encode(payload, auth.settings.jwt_secret_key, algorithm=auth.settings.jwt_algorithm)
        with pytest.raises(jwt.InvalidTokenError, match="role does not match"):
            auth.verify_token(token)

    def test_token_for_inactive_user_raises(self, auth: AuthService) -> None:
        """Token for a user not in the registry raises."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "nonexistent-user",
            "role": "Admin",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "jti": "no-user",
        }
        token = jwt.encode(payload, auth.settings.jwt_secret_key, algorithm=auth.settings.jwt_algorithm)
        with pytest.raises(jwt.InvalidTokenError, match="inactive or missing"):
            auth.verify_token(token)

    def test_authenticate_wrong_password_returns_none(self, auth: AuthService) -> None:
        result = auth.authenticate("demo-admin", "definitely-wrong")
        assert result is None

    def test_authenticate_unknown_user_returns_none(self, auth: AuthService) -> None:
        result = auth.authenticate("no-such-user", "password")
        assert result is None

    def test_pbkdf2_verify_correct(self, auth: AuthService) -> None:
        hashed = auth.hash_password_pbkdf2("test-pass", salt="salt123")
        assert auth._verify_password(hashed, "test-pass") is True
        assert auth._verify_password(hashed, "wrong-pass") is False

    def test_legacy_unsalted_hash_is_rejected(self, auth: AuthService) -> None:
        legacy_hash = "0" * 64
        assert auth._verify_password(legacy_hash, "test-pass") is False

    def test_under_iteration_pbkdf2_hash_is_rejected(self, auth: AuthService) -> None:
        under_iteration_hash = f"pbkdf2_sha256$1$salt123${'0' * 64}"
        assert auth._verify_password(under_iteration_hash, "test-pass") is False

    def test_malformed_pbkdf2_hash_returns_false(self, auth: AuthService) -> None:
        assert auth._verify_password("pbkdf2_sha256$not$enough", "any") is False
        assert auth._verify_password("pbkdf2_sha256$notanumber$salt$hex", "any") is False


# ---------------------------------------------------------------------------
# Login Attempt Guard (with race condition awareness)
# ---------------------------------------------------------------------------


class TestLoginAttemptGuard:
    """Tests for LoginAttemptGuard including thread safety."""

    def test_basic_lockout_flow(self) -> None:
        guard = LoginAttemptGuard(max_failures=3, window_seconds=300, lock_seconds=60)
        locked, _ = guard.check_locked("user1")
        assert locked is False

        guard.register_failure("user1")
        guard.register_failure("user1")
        result = guard.register_failure("user1")
        assert result["locked"] is True
        assert result["retry_after_seconds"] == 60

        locked, remaining = guard.check_locked("user1")
        assert locked is True
        assert remaining > 0

    def test_success_clears_failures(self) -> None:
        guard = LoginAttemptGuard(max_failures=3, window_seconds=300, lock_seconds=60)
        guard.register_failure("user1")
        guard.register_failure("user1")
        guard.register_success("user1")

        locked, _ = guard.check_locked("user1")
        assert locked is False

        # After success reset, two more failures should not lock
        guard.register_failure("user1")
        guard.register_failure("user1")
        result = guard.register_failure("user1")
        assert result["locked"] is True

    def test_configure_clears_state(self) -> None:
        guard = LoginAttemptGuard(max_failures=2, window_seconds=300, lock_seconds=60)
        guard.register_failure("user1")
        guard.register_failure("user1")
        locked, _ = guard.check_locked("user1")
        assert locked is True

        guard.configure(max_failures=5, window_seconds=300, lock_seconds=60)
        locked, _ = guard.check_locked("user1")
        assert locked is False

    def test_reset_clears_all_state(self) -> None:
        guard = LoginAttemptGuard(max_failures=2, window_seconds=300, lock_seconds=60)
        guard.register_failure("user1")
        guard.register_failure("user1")
        guard.reset()
        locked, _ = guard.check_locked("user1")
        assert locked is False

    def test_different_principals_are_independent(self) -> None:
        guard = LoginAttemptGuard(max_failures=2, window_seconds=300, lock_seconds=60)
        guard.register_failure("user1")
        guard.register_failure("user1")
        locked_user1, _ = guard.check_locked("user1")
        locked_user2, _ = guard.check_locked("user2")
        assert locked_user1 is True
        assert locked_user2 is False

    def test_concurrent_failures_thread_safety(self) -> None:
        """Verify guard does not corrupt state under concurrent access."""
        guard = LoginAttemptGuard(max_failures=100, window_seconds=300, lock_seconds=60)
        errors: list[str] = []

        def register_failures(principal: str, count: int) -> None:
            try:
                for _ in range(count):
                    guard.register_failure(principal)
            except RuntimeError as exc:
                errors.append(str(exc))

        threads = []
        for i in range(10):
            t = threading.Thread(target=register_failures, args=(f"user-{i % 3}", 20))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"

        # Verify internal state is consistent
        for principal_id in range(3):
            principal = f"user-{principal_id}"
            entry = guard._state.get(principal)
            if entry:
                assert isinstance(entry["failures"], list)

    def test_concurrent_failure_and_success_no_crash(self) -> None:
        """Concurrent register_failure and register_success should not crash."""
        guard = LoginAttemptGuard(max_failures=50, window_seconds=300, lock_seconds=60)
        errors: list[str] = []

        def fail_loop() -> None:
            try:
                for _ in range(50):
                    guard.register_failure("shared-user")
            except RuntimeError as exc:
                errors.append(str(exc))

        def success_loop() -> None:
            try:
                for _ in range(50):
                    guard.register_success("shared-user")
            except RuntimeError as exc:
                errors.append(str(exc))

        t1 = threading.Thread(target=fail_loop)
        t2 = threading.Thread(target=success_loop)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0

    def test_remaining_attempts_count(self) -> None:
        guard = LoginAttemptGuard(max_failures=3, window_seconds=300, lock_seconds=60)
        result = guard.register_failure("user1")
        assert result["remaining_attempts"] == 2
        assert result["failure_count_in_window"] == 1

        result = guard.register_failure("user1")
        assert result["remaining_attempts"] == 1

        result = guard.register_failure("user1")
        assert result["remaining_attempts"] == 0
        assert result["locked"] is True


# ---------------------------------------------------------------------------
# Export Signature Verification
# ---------------------------------------------------------------------------


class TestExportSignature:
    """Tests for _export_signature_headers with signing enabled and disabled."""

    def test_signing_enabled_produces_hmac(self) -> None:
        original_enabled = settings.export_signing_enabled
        original_key = settings.export_signing_key
        original_key_id = settings.export_signing_key_id
        try:
            settings.export_signing_enabled = True
            settings.export_signing_key = "dddddddddddddddddddddddddddddddd"
            settings.export_signing_key_id = "test-key-v1"

            payload = b'{"test": "data"}'
            headers = _export_signature_headers(payload)

            assert headers["X-Export-Signature-Alg"] == "hmac-sha256"
            assert headers["X-Export-Signature-Key-Id"] == "test-key-v1"
            assert headers["X-Export-SHA256"] == hashlib.sha256(payload).hexdigest()

            expected_sig = hmac_mod.new(
                settings.export_signing_key.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()
            assert headers["X-Export-Signature"] == expected_sig
        finally:
            settings.export_signing_enabled = original_enabled
            settings.export_signing_key = original_key
            settings.export_signing_key_id = original_key_id

    def test_signing_disabled_uses_none(self) -> None:
        original_enabled = settings.export_signing_enabled
        try:
            settings.export_signing_enabled = False

            payload = b'{"test": "data"}'
            headers = _export_signature_headers(payload)

            assert headers["X-Export-Signature-Alg"] == "none"
            assert headers["X-Export-Signature-Key-Id"] == "none"
            assert headers["X-Export-Signature"] == ""
            assert headers["X-Export-SHA256"] == hashlib.sha256(payload).hexdigest()
        finally:
            settings.export_signing_enabled = original_enabled

    def test_empty_payload_still_produces_valid_sha256(self) -> None:
        original_enabled = settings.export_signing_enabled
        try:
            settings.export_signing_enabled = False
            headers = _export_signature_headers(b"")
            assert headers["X-Export-SHA256"] == hashlib.sha256(b"").hexdigest()
        finally:
            settings.export_signing_enabled = original_enabled

    def test_signature_changes_with_different_payload(self) -> None:
        original_enabled = settings.export_signing_enabled
        original_key = settings.export_signing_key
        try:
            settings.export_signing_enabled = True
            settings.export_signing_key = "dddddddddddddddddddddddddddddddd"

            h1 = _export_signature_headers(b"payload-a")
            h2 = _export_signature_headers(b"payload-b")
            assert h1["X-Export-SHA256"] != h2["X-Export-SHA256"]
            assert h1["X-Export-Signature"] != h2["X-Export-Signature"]
        finally:
            settings.export_signing_enabled = original_enabled
            settings.export_signing_key = original_key


# ---------------------------------------------------------------------------
# Pipeline Stages (CotOrchestrator)
# ---------------------------------------------------------------------------


class TestCotOrchestrator:
    """Tests for the three-stage CoT orchestrator in deterministic mode."""

    @pytest.fixture()
    def sample_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "관리번호": "PJT-001",
                    "사업명": "테스트",
                    "담당자": "홍길동",
                    "사업비": 1000000,
                    "진행률": 50,
                    "상태": "진행중",
                    "보고일자": "2026-02-19",
                }
            ]
        )

    @pytest.fixture()
    def contract(self) -> DataContract:
        loader = SpecKitLoader(base_path=Path("specs"))
        return loader.load_contract("default")

    @pytest.fixture()
    def profile(self) -> CleanupProfile:
        loader = SpecKitLoader(base_path=Path("specs"))
        return loader.load_profile("default")

    def test_deterministic_mode_runs_all_three_stages(
        self, sample_df: pd.DataFrame, contract: DataContract, profile: CleanupProfile
    ) -> None:
        orchestrator = CotOrchestrator(llm_service=None, enable_llm=False)
        result = orchestrator.run(sample_df, contract, profile)

        assert isinstance(result, CotResult)
        assert len(result.trace) == 3
        assert "stage1:schema_inference completed" in result.trace
        assert "stage2:cleanup_advice completed" in result.trace
        assert "stage3:document_mapping completed" in result.trace

    def test_schema_inference_maps_columns(
        self, sample_df: pd.DataFrame, contract: DataContract
    ) -> None:
        orchestrator = CotOrchestrator(llm_service=None, enable_llm=False)
        result = orchestrator._stage_schema_inference(sample_df, contract)
        assert result["mode"] == "deterministic"
        field_map = result["field_map"]
        assert "사업명" in field_map

    def test_cleanup_advice_identifies_missing_columns(self, profile: CleanupProfile) -> None:
        df_with_missing = pd.DataFrame(
            {
                "col_a": [1, None, None, None, None],
                "col_b": [1, 2, 3, 4, 5],
            }
        )
        orchestrator = CotOrchestrator(llm_service=None, enable_llm=False)
        result = orchestrator._stage_cleanup_advice(df_with_missing, profile)
        assert result["mode"] == "deterministic"
        assert "col_a" in result["advice"]["high_missing_columns"]
        assert "col_b" not in result["advice"]["high_missing_columns"]

    def test_document_mapping_includes_row_count(
        self, sample_df: pd.DataFrame, profile: CleanupProfile
    ) -> None:
        orchestrator = CotOrchestrator(llm_service=None, enable_llm=False)
        result = orchestrator._stage_document_mapping(sample_df, profile)
        assert result["mode"] == "deterministic"
        assert result["payload"]["{{ROW_COUNT}}"] == 1

    def test_document_mapping_empty_dataframe(self, profile: CleanupProfile) -> None:
        empty_df = pd.DataFrame()
        orchestrator = CotOrchestrator(llm_service=None, enable_llm=False)
        result = orchestrator._stage_document_mapping(empty_df, profile)
        assert result["payload"]["{{ROW_COUNT}}"] == 0

    def test_stage_outputs_keys(
        self, sample_df: pd.DataFrame, contract: DataContract, profile: CleanupProfile
    ) -> None:
        orchestrator = CotOrchestrator(llm_service=None, enable_llm=False)
        result = orchestrator.run(sample_df, contract, profile)
        assert "schema_inference" in result.stage_outputs
        assert "cleanup_advice" in result.stage_outputs
        assert "document_mapping" in result.stage_outputs

    def test_normalize_strips_and_lowercases(self) -> None:
        assert CotOrchestrator._normalize("  Hello World  ") == "helloworld"
        assert CotOrchestrator._normalize("관리번호") == "관리번호"

    def test_safe_json_handles_all_types(self) -> None:
        assert CotOrchestrator._safe_json("hello") == "hello"
        assert CotOrchestrator._safe_json(42) == 42
        assert CotOrchestrator._safe_json(3.14) == 3.14
        assert CotOrchestrator._safe_json(True) is True
        assert CotOrchestrator._safe_json(None) is None
        assert isinstance(CotOrchestrator._safe_json([1, 2]), str)
        assert isinstance(CotOrchestrator._safe_json({"a": 1}), str)


# ---------------------------------------------------------------------------
# Path Guardrails Validation
# ---------------------------------------------------------------------------


class TestPathGuardrails:
    """Tests for path resolution and guardrail enforcement."""

    def test_resolve_relative_path(self) -> None:
        resolved = _resolve_repo_path("examples/input/test.xlsx")
        assert resolved.is_absolute()
        assert str(resolved).endswith("examples/input/test.xlsx")

    def test_resolve_absolute_path(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.xlsx"
        resolved = _resolve_repo_path(str(test_file))
        assert resolved == test_file

    def test_assert_path_within_base_valid(self) -> None:
        result = _assert_path_within_base(
            "examples/input/sample_projects.xlsx",
            "examples/input",
            "input_path",
        )
        assert result.is_absolute()

    def test_assert_path_traversal_blocked(self) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _assert_path_within_base(
                "../README.md",
                "examples/input",
                "input_path",
            )
        assert exc_info.value.status_code == 400
        assert "input_path" in exc_info.value.detail

    def test_assert_output_dir_traversal_blocked(self) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _assert_path_within_base(
                "/tmp/evil",
                "examples/output",
                "output_dir",
            )
        assert exc_info.value.status_code == 400

    def test_assert_path_rejects_prefix_collision(self, tmp_path: Path) -> None:
        from fastapi import HTTPException

        allowed = tmp_path / "allowed"
        sibling = tmp_path / "allowed-evil" / "report.xlsx"
        with pytest.raises(HTTPException):
            _assert_path_within_base(str(sibling), str(allowed), "input_path")

    def test_assert_path_rejects_before_resolving_outside_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import os

        from fastapi import HTTPException

        allowed = tmp_path / "allowed"
        outside = tmp_path / "outside" / "report.xlsx"
        resolved_paths: list[str] = []
        original_realpath = os.path.realpath

        def recording_realpath(path: str) -> str:
            resolved_paths.append(path)
            return original_realpath(path)

        monkeypatch.setattr(os.path, "realpath", recording_realpath)
        with pytest.raises(HTTPException):
            _assert_path_within_base(str(outside), str(allowed), "input_path")

        assert resolved_paths == []

    def test_assert_path_rejects_symlink_escape(self, tmp_path: Path) -> None:
        from fastapi import HTTPException

        allowed = tmp_path / "allowed"
        outside = tmp_path / "outside"
        allowed.mkdir()
        outside.mkdir()
        escape_link = allowed / "escape"
        try:
            escape_link.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are not available on this platform")

        with pytest.raises(HTTPException):
            _assert_path_within_base(
                str(escape_link / "report.xlsx"),
                str(allowed),
                "input_path",
            )

    def test_assert_path_accepts_configured_base_itself(self, tmp_path: Path) -> None:
        allowed = tmp_path / "allowed"
        allowed.mkdir()

        assert _assert_path_within_base(str(allowed), str(allowed), "output_dir") == allowed

    def test_process_output_directory_is_not_created_through_symlink(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from fastapi import HTTPException

        allowed = tmp_path / "allowed"
        outside = tmp_path / "outside"
        allowed.mkdir()
        outside.mkdir()
        escape_link = allowed / "escape"
        try:
            escape_link.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are not available on this platform")
        monkeypatch.setattr(settings, "allowed_output_base_dir", str(allowed))

        with pytest.raises(HTTPException):
            _validate_process_path_request(
                input_path="examples/input/sample_projects.xlsx",
                output_dir=str(escape_link / "created"),
                template_path=None,
            )

        assert not (outside / "created").exists()

    def test_upload_output_directory_is_not_created_through_symlink(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from fastapi import HTTPException

        allowed = tmp_path / "allowed"
        outside = tmp_path / "outside"
        allowed.mkdir()
        outside.mkdir()
        escape_link = allowed / "escape"
        try:
            escape_link.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("Directory symlinks are not available on this platform")
        monkeypatch.setattr(settings, "allowed_output_base_dir", str(allowed))

        with pytest.raises(HTTPException):
            _validate_upload_request_paths(
                output_dir=str(escape_link / "created"),
                template_path=None,
            )

        assert not (outside / "created").exists()

    def test_validate_process_path_request_rejects_all_traversals(self) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            _validate_process_path_request(
                input_path="../../../etc/passwd",
                output_dir="examples/output",
                template_path=None,
            )

    def test_validate_process_path_request_rejects_template_traversal(self) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            _validate_process_path_request(
                input_path="examples/input/sample_projects.xlsx",
                output_dir="examples/output",
                template_path="../../etc/shadow",
            )

    def test_validate_process_path_request_accepts_valid_paths(self) -> None:
        inp, out, tpl = _validate_process_path_request(
            input_path="examples/input/sample_projects.xlsx",
            output_dir="examples/output",
            template_path="examples/input/sample_report_template.txt",
        )
        assert Path(inp).is_absolute()
        assert Path(out).is_absolute()
        assert tpl is not None and Path(tpl).is_absolute()

    def test_validate_process_path_request_none_template(self) -> None:
        inp, out, tpl = _validate_process_path_request(
            input_path="examples/input/sample_projects.xlsx",
            output_dir="examples/output",
            template_path=None,
        )
        assert tpl is None
