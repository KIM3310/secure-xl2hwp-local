from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class LocalLLMService:
    def __init__(
        self,
        base_url: str,
        primary_model: str,
        fallback_model: str,
        timeout_seconds: int = 45,
        unavailable_cooldown_seconds: int = 20,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.timeout_seconds = timeout_seconds
        self.unavailable_cooldown_seconds = max(0, unavailable_cooldown_seconds)
        self._unavailable_until_monotonic = 0.0

    def chat_json(self, system_prompt: str, user_prompt: str) -> Optional[dict[str, Any]]:
        if self._is_in_unavailable_cooldown():
            return None

        response = self._invoke(self.primary_model, system_prompt, user_prompt)
        if response is not None:
            return response

        if self._is_in_unavailable_cooldown():
            return None

        return self._invoke(self.fallback_model, system_prompt, user_prompt)

    def _is_in_unavailable_cooldown(self) -> bool:
        return time.monotonic() < self._unavailable_until_monotonic

    def _set_unavailable_cooldown(self) -> None:
        if self.unavailable_cooldown_seconds <= 0:
            return
        self._unavailable_until_monotonic = time.monotonic() + self.unavailable_cooldown_seconds

    def _invoke(self, model: str, system_prompt: str, user_prompt: str) -> Optional[dict[str, Any]]:
        if self._is_in_unavailable_cooldown():
            return None

        payload = {
            "model": model,
            "format": "json",
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                raw = response.json()

            content = raw.get("message", {}).get("content", "")
            if not content:
                logger.warning("Empty LLM response from model=%s", model)
                return None
            parsed: dict[str, Any] = json.loads(content)
            self._unavailable_until_monotonic = 0.0
            return parsed
        except httpx.TransportError as exc:  # pragma: no cover - network and runtime variability
            self._set_unavailable_cooldown()
            logger.warning("LLM transport failed model=%s error=%s", model, exc)
            return None
        except httpx.HTTPError as exc:  # pragma: no cover - network and runtime variability
            logger.warning("LLM HTTP failed model=%s error=%s", model, exc)
            return None
        except (json.JSONDecodeError, ValueError, KeyError) as exc:  # pragma: no cover - network and runtime variability
            logger.warning("LLM invocation failed model=%s error=%s", model, exc)
            return None
