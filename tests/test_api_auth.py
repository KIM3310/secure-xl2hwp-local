import io

from fastapi.testclient import TestClient

from app.main import app, login_attempt_guard, settings

client = TestClient(app)


def test_login_and_me_endpoint() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["user_id"] == "demo-admin"


def test_me_requires_token() -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_process_path_requires_token() -> None:
    response = client.post(
        "/process/path",
        json={
            "input_path": "examples/input/sample_projects.xlsx",
            "output_dir": "examples/output",
            "contract_name": "default",
            "profile_name": "default",
            "template_name": "default",
            "template_path": "examples/input/sample_report_template.txt",
        },
    )
    assert response.status_code == 401


def test_process_path_with_token() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/process/path",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "input_path": "examples/input/sample_projects.xlsx",
            "output_dir": "examples/output",
            "contract_name": "default",
            "profile_name": "default",
            "template_name": "default",
            "template_path": "examples/input/sample_report_template.txt",
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_process_path_file_not_found_returns_404() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/process/path",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "input_path": "examples/input/not_found.xlsx",
            "output_dir": "examples/output",
            "contract_name": "default",
            "profile_name": "default",
            "template_name": "default",
            "template_path": "examples/input/sample_report_template.txt",
        },
    )
    assert response.status_code == 404
    assert "request_id" in response.json()["detail"]


def test_role_restriction_for_process_endpoint() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-auditor", "password": "auditor123!"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/process/path",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "input_path": "examples/input/sample_projects.xlsx",
            "output_dir": "examples/output",
            "contract_name": "default",
            "profile_name": "default",
            "template_name": "default",
            "template_path": "examples/input/sample_report_template.txt",
        },
    )
    assert response.status_code == 403


def test_process_file_size_limit() -> None:
    login_response = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    token = login_response.json()["access_token"]

    original_limit = settings.max_upload_mb
    settings.max_upload_mb = 1
    try:
        large_content = io.BytesIO(b"x" * (2 * 1024 * 1024))
        response = client.post(
            "/process/file",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("too_large.xlsx", large_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 413
    finally:
        settings.max_upload_mb = original_limit


def test_login_rate_limit_lockout() -> None:
    original = (
        settings.auth_login_max_failures,
        settings.auth_login_window_seconds,
        settings.auth_login_lock_seconds,
    )
    settings.auth_login_max_failures = 2
    settings.auth_login_window_seconds = 300
    settings.auth_login_lock_seconds = 120
    login_attempt_guard.configure(
        max_failures=settings.auth_login_max_failures,
        window_seconds=settings.auth_login_window_seconds,
        lock_seconds=settings.auth_login_lock_seconds,
    )
    try:
        first = client.post(
            "/auth/login",
            json={"user_id": "demo-admin", "password": "wrong-password"},
        )
        assert first.status_code == 401

        second = client.post(
            "/auth/login",
            json={"user_id": "demo-admin", "password": "wrong-password"},
        )
        assert second.status_code == 429
        detail = second.json()["detail"]
        assert detail["message"] == "Too many failed login attempts"
        assert detail["retry_after_seconds"] > 0

        blocked = client.post(
            "/auth/login",
            json={"user_id": "demo-admin", "password": "admin123!"},
        )
        assert blocked.status_code == 429
    finally:
        settings.auth_login_max_failures, settings.auth_login_window_seconds, settings.auth_login_lock_seconds = (
            original
        )
        login_attempt_guard.configure(
            max_failures=settings.auth_login_max_failures,
            window_seconds=settings.auth_login_window_seconds,
            lock_seconds=settings.auth_login_lock_seconds,
        )


def test_login_success_resets_rate_limit_counter() -> None:
    original = (
        settings.auth_login_max_failures,
        settings.auth_login_window_seconds,
        settings.auth_login_lock_seconds,
    )
    settings.auth_login_max_failures = 2
    settings.auth_login_window_seconds = 300
    settings.auth_login_lock_seconds = 120
    login_attempt_guard.configure(
        max_failures=settings.auth_login_max_failures,
        window_seconds=settings.auth_login_window_seconds,
        lock_seconds=settings.auth_login_lock_seconds,
    )
    try:
        first_fail = client.post(
            "/auth/login",
            json={"user_id": "demo-admin", "password": "wrong-password"},
        )
        assert first_fail.status_code == 401

        success = client.post(
            "/auth/login",
            json={"user_id": "demo-admin", "password": "admin123!"},
        )
        assert success.status_code == 200

        fail_after_success = client.post(
            "/auth/login",
            json={"user_id": "demo-admin", "password": "wrong-password"},
        )
        assert fail_after_success.status_code == 401
    finally:
        settings.auth_login_max_failures, settings.auth_login_window_seconds, settings.auth_login_lock_seconds = (
            original
        )
        login_attempt_guard.configure(
            max_failures=settings.auth_login_max_failures,
            window_seconds=settings.auth_login_window_seconds,
            lock_seconds=settings.auth_login_lock_seconds,
        )


def test_auth_guard_state_requires_audit_role() -> None:
    analyst_login = client.post(
        "/auth/login",
        json={"user_id": "demo-analyst", "password": "analyst123!"},
    )
    analyst_token = analyst_login.json()["access_token"]
    forbidden = client.get(
        "/auth/guard/state",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert forbidden.status_code == 403


def test_auth_guard_state_with_admin_role() -> None:
    admin_login = client.post(
        "/auth/login",
        json={"user_id": "demo-admin", "password": "admin123!"},
    )
    admin_token = admin_login.json()["access_token"]
    response = client.get(
        "/auth/guard/state",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["max_failures"] >= 1
    assert payload["window_seconds"] >= 10
    assert payload["lock_seconds"] >= 1
