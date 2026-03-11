"""Async OpenRouter API client for LLM calls."""

from __future__ import annotations

import json
import logging
import re

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import OPENROUTER_BASE_URL, get_openrouter_key, MODEL_FAST, MODEL_REASONING

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Async wrapper around the OpenRouter chat completions API."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self.total_tokens_used = 0

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120),
                headers={
                    "Authorization": f"Bearer {get_openrouter_key()}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://seoptimize.com",
                    "X-Title": "ICP Generator",
                }
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((aiohttp.ClientError, TimeoutError)),
    )
    async def chat(
        self,
        messages: list[dict],
        model: str = MODEL_FAST,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: str | None = None,
    ) -> str:
        """Send a chat completion request and return the response text."""
        session = await self._get_session()

        payload: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        async with session.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            json=payload,
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                logger.error("OpenRouter error %s: %s", resp.status, body)
                raise aiohttp.ClientResponseError(
                    resp.request_info,
                    resp.history,
                    status=resp.status,
                    message=body,
                )
            data = await resp.json()

        usage = data.get("usage", {})
        self.total_tokens_used += usage.get("total_tokens", 0)

        return data["choices"][0]["message"]["content"]

    async def chat_json(
        self,
        messages: list[dict],
        model: str = MODEL_FAST,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """Send a chat request and parse the response as JSON."""
        raw = await self.chat(
            messages, model=model, temperature=temperature,
            max_tokens=max_tokens, response_format="json",
        )
        return _extract_json(raw)

    async def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = MODEL_FAST,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Convenience: system + user message, return text."""
        return await self.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def analyze_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = MODEL_FAST,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> dict:
        """Convenience: system + user message, return parsed JSON."""
        return await self.chat_json(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )


def _extract_json(text: str) -> dict:
    """Extract JSON from an LLM response that may be wrapped in markdown."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    logger.error("Failed to extract JSON from response: %s", text[:500])
    return {}
