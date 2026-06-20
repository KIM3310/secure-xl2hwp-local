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
        provider: str = "ollama",
        api_key: str = "",
        http_referer: str = "",
        app_title: str = "",
        timeout_seconds: int = 45,
        unavailable_cooldown_seconds: int = 20,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.provider = provider.strip().lower() or "ollama"
        self.api_key = api_key.strip()
        self.http_referer = http_referer.strip()
        self.app_title = app_title.strip()
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
        if self.provider == "openrouter" and not self.api_key:
            logger.warning("OpenRouter LLM provider selected but OPENROUTER_API_KEY is missing")
            return None

        payload = self._build_payload(model, system_prompt, user_prompt)
        headers = self._build_headers()
        url = self._chat_url()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                raw = response.json()

            content = self._extract_content(raw)
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

    def _chat_url(self) -> str:
        if self.provider == "openrouter":
            return f"{self.base_url}/chat/completions"
        return f"{self.base_url}/api/chat"

    def _build_headers(self) -> dict[str, str]:
        if self.provider != "openrouter":
            return {}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.app_title:
            headers["X-OpenRouter-Title"] = self.app_title
        return headers

    def _build_payload(self, model: str, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\nRespond only with valid JSON."},
            {"role": "user", "content": user_prompt},
        ]
        if self.provider == "openrouter":
            return {
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1200,
            }
        return {
            "model": model,
            "format": "json",
            "stream": False,
            "messages": messages,
        }

    def _extract_content(self, raw: dict[str, Any]) -> str:
        if self.provider == "openrouter":
            choices = raw.get("choices")
            if isinstance(choices, list) and choices:
                message = choices[0].get("message") if isinstance(choices[0], dict) else None
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
            return ""
        content = raw.get("message", {}).get("content", "")
        return content if isinstance(content, str) else ""
