"""Async DataForSEO API client for SERP and content parsing."""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import (
    DATAFORSEO_BASE_URL,
    get_dataforseo_credentials,
    MAX_CONCURRENT_API_CALLS,
    MIN_API_DELAY_SECONDS,
)

logger = logging.getLogger(__name__)


class DataForSEOClient:
    """Async wrapper for DataForSEO SERP and On-Page APIs."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)
        self._last_call_time: float = 0
        self.total_api_calls = 0

    def _get_auth_header(self) -> str:
        login, password = get_dataforseo_credentials()
        credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
        return f"Basic {credentials}"

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": self._get_auth_header(),
                    "Content-Type": "application/json",
                }
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _rate_limited_request(
        self, method: str, url: str, payload: list[dict]
    ) -> dict:
        """Make a rate-limited API request."""
        async with self._semaphore:
            # Enforce minimum delay between calls
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_call_time
            if elapsed < MIN_API_DELAY_SECONDS:
                await asyncio.sleep(MIN_API_DELAY_SECONDS - elapsed)

            session = await self._get_session()
            self._last_call_time = asyncio.get_event_loop().time()
            self.total_api_calls += 1

            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("DataForSEO error %s: %s", resp.status, body)
                    raise aiohttp.ClientResponseError(
                        resp.request_info,
                        resp.history,
                        status=resp.status,
                        message=body,
                    )
                return await resp.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type((aiohttp.ClientError, TimeoutError)),
    )
    async def serp_search(
        self,
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en",
        depth: int = 10,
    ) -> list[dict]:
        """Search Google SERP and return organic results.

        Returns a list of result dicts with keys: url, title, description, position.
        """
        url = f"{DATAFORSEO_BASE_URL}/serp/google/organic/live/advanced"
        payload = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "depth": depth,
            }
        ]

        data = await self._rate_limited_request("POST", url, payload)
        results = []

        try:
            tasks = data.get("tasks", [])
            if not tasks:
                return results
            task_result = tasks[0].get("result", [])
            if not task_result:
                return results

            items = task_result[0].get("items", [])
            for item in items:
                if item.get("type") == "organic":
                    results.append(
                        {
                            "url": item.get("url", ""),
                            "title": item.get("title", ""),
                            "description": item.get("description", ""),
                            "position": item.get("rank_absolute", 0),
                        }
                    )
        except (IndexError, KeyError, TypeError) as e:
            logger.warning("Error parsing SERP results for '%s': %s", keyword, e)

        return results

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, TimeoutError)),
    )
    async def parse_content(self, target_url: str) -> str:
        """Parse and extract text content from a URL.

        Returns the plain text content of the page (truncated to max length).
        """
        url = f"{DATAFORSEO_BASE_URL}/on_page/content_parsing/live"
        payload = [{"url": target_url}]

        data = await self._rate_limited_request("POST", url, payload)

        try:
            tasks = data.get("tasks", [])
            if not tasks:
                return ""
            task_result = tasks[0].get("result", [])
            if not task_result:
                return ""

            items = task_result[0].get("items", [])
            if not items:
                return ""

            page_content = items[0].get("page_content", {})

            # Combine heading and body text
            parts = []
            if page_content.get("header"):
                header = page_content["header"]
                if isinstance(header, dict):
                    for key in ["title", "h1", "h2", "h3"]:
                        val = header.get(key)
                        if val:
                            if isinstance(val, list):
                                parts.extend(val)
                            else:
                                parts.append(str(val))

            body_text = page_content.get("plain_text_by_paragraphs")
            if body_text and isinstance(body_text, list):
                parts.extend([p for p in body_text if isinstance(p, str)])

            content = "\n".join(parts)
            from config.settings import MAX_CONTENT_LENGTH
            return content[:MAX_CONTENT_LENGTH]

        except (IndexError, KeyError, TypeError) as e:
            logger.warning("Error parsing content from '%s': %s", target_url, e)
            return ""
