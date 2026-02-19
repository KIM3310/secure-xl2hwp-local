import time

import httpx

from app.services.llm_service import LocalLLMService


def _build_service(cooldown_seconds: int = 20) -> LocalLLMService:
    return LocalLLMService(
        base_url="http://127.0.0.1:11434",
        primary_model="qwen2.5:7b",
        fallback_model="qwen2.5:14b",
        timeout_seconds=1,
        unavailable_cooldown_seconds=cooldown_seconds,
    )


def test_transport_error_enters_cooldown_and_skips_fallback(monkeypatch) -> None:
    call_counter = {"count": 0}

    class FailingClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, *args, **kwargs):
            call_counter["count"] += 1
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.services.llm_service.httpx.Client", FailingClient)

    service = _build_service(cooldown_seconds=60)

    assert service.chat_json("system", "user") is None
    assert call_counter["count"] == 1

    # second request is suppressed by cooldown, so no additional network attempt
    assert service.chat_json("system", "user") is None
    assert call_counter["count"] == 1


def test_http_error_does_not_enter_cooldown_and_tries_fallback(monkeypatch) -> None:
    call_counter = {"count": 0}

    class HttpErrorClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, *args, **kwargs):
            call_counter["count"] += 1
            request = httpx.Request("POST", "http://127.0.0.1:11434/api/chat")
            response = httpx.Response(status_code=500, request=request)
            raise httpx.HTTPStatusError("upstream failure", request=request, response=response)

    monkeypatch.setattr("app.services.llm_service.httpx.Client", HttpErrorClient)

    service = _build_service(cooldown_seconds=60)
    assert service.chat_json("system", "user") is None
    assert call_counter["count"] == 2
    assert service._unavailable_until_monotonic == 0.0


def test_successful_call_clears_existing_cooldown(monkeypatch) -> None:
    call_counter = {"count": 0}

    class SuccessfulResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"message": {"content": "{\"ok\": true}"}}

    class SuccessClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, *args, **kwargs):
            call_counter["count"] += 1
            return SuccessfulResponse()

    monkeypatch.setattr("app.services.llm_service.httpx.Client", SuccessClient)

    service = _build_service(cooldown_seconds=60)
    service._unavailable_until_monotonic = time.monotonic() + 30

    # while in cooldown, network call is skipped
    assert service.chat_json("system", "user") is None
    assert call_counter["count"] == 0

    service._unavailable_until_monotonic = 0.0
    result = service.chat_json("system", "user")
    assert result == {"ok": True}
    assert call_counter["count"] == 1
    assert service._unavailable_until_monotonic == 0.0
