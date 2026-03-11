"""Synchronous DataForSEO API client for SERP and content parsing."""

from __future__ import annotations

import logging
import threading
import time

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import (
    DATAFORSEO_BASE_URL,
    get_dataforseo_credentials,
    MIN_API_DELAY_SECONDS,
    MAX_CONTENT_LENGTH,
)

logger = logging.getLogger(__name__)


class DataForSEOClient:
    """Sync wrapper for DataForSEO SERP and On-Page APIs."""

    def __init__(self) -> None:
        self._session: requests.Session | None = None
        self._lock = threading.Lock()
        self._last_call_time: float = 0
        self.total_api_calls = 0

    def _get_session(self) -> requests.Session:
        if self._session is None:
            login, password = get_dataforseo_credentials()
            self._session = requests.Session()
            self._session.auth = (login, password)
            self._session.headers.update({"Content-Type": "application/json"})
        return self._session

    def close(self) -> None:
        if self._session:
            self._session.close()
            self._session = None

    def _rate_limited_request(self, url: str, payload: list[dict]) -> dict:
        """Make a rate-limited API request (thread-safe)."""
        with self._lock:
            elapsed = time.time() - self._last_call_time
            if elapsed < MIN_API_DELAY_SECONDS:
                time.sleep(MIN_API_DELAY_SECONDS - elapsed)

            session = self._get_session()
            self._last_call_time = time.time()
            self.total_api_calls += 1

        resp = session.post(url, json=payload, timeout=60)

        if resp.status_code != 200:
            logger.error("DataForSEO error %s: %s", resp.status_code, resp.text[:500])
            resp.raise_for_status()

        return resp.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type((requests.RequestException, TimeoutError)),
    )
    def serp_search(
        self,
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en",
        depth: int = 10,
    ) -> list[dict]:
        """Search Google SERP and return organic results."""
        url = f"{DATAFORSEO_BASE_URL}/serp/google/organic/live/advanced"
        payload = [
            {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "depth": depth,
            }
        ]

        data = self._rate_limited_request(url, payload)
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
        retry=retry_if_exception_type((requests.RequestException, TimeoutError)),
    )
    def parse_content(self, target_url: str) -> str:
        """Parse and extract text content from a URL."""
        url = f"{DATAFORSEO_BASE_URL}/on_page/content_parsing/live"
        payload = [{"url": target_url}]

        data = self._rate_limited_request(url, payload)

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
            return content[:MAX_CONTENT_LENGTH]

        except (IndexError, KeyError, TypeError) as e:
            logger.warning("Error parsing content from '%s': %s", target_url, e)
            return ""
