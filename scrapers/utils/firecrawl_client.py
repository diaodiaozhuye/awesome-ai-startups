"""Firecrawl MCP wrapper with rate limiting and daily quota tracking.

Provides a unified interface for all scrapers that need to fetch
JavaScript-rendered or anti-bot-protected web pages via Firecrawl.
Enforces the slow-and-steady crawl principle with daily page limits.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx

from scrapers.config import (
    DATA_DIR,
    DEFAULT_REQUEST_DELAY,
    MAX_DAILY_FIRECRAWL_PAGES,
    MAX_RETRIES,
)

logger = logging.getLogger(__name__)

# File to persist daily usage across scraper runs
_USAGE_FILE = DATA_DIR / ".firecrawl_usage.json"


@dataclass
class FirecrawlUsage:
    """Tracks daily Firecrawl page usage."""

    date: str = ""
    pages_used: int = 0

    def can_fetch(self) -> bool:
        """Check if we are within the daily quota."""
        today = date.today().isoformat()
        if self.date != today:
            # New day — reset counter
            self.date = today
            self.pages_used = 0
        return self.pages_used < MAX_DAILY_FIRECRAWL_PAGES

    def record_fetch(self) -> None:
        """Record one page fetch."""
        today = date.today().isoformat()
        if self.date != today:
            self.date = today
            self.pages_used = 0
        self.pages_used += 1

    @property
    def remaining(self) -> int:
        today = date.today().isoformat()
        if self.date != today:
            return MAX_DAILY_FIRECRAWL_PAGES
        return max(0, MAX_DAILY_FIRECRAWL_PAGES - self.pages_used)


@dataclass
class FirecrawlResult:
    """Result from a Firecrawl page fetch."""

    url: str
    markdown: str = ""
    html: str = ""
    metadata: dict = field(default_factory=dict)
    success: bool = True
    error: str | None = None


class FirecrawlClient:
    """Rate-limited Firecrawl client with daily quota enforcement.

    Usage::

        client = FirecrawlClient()
        result = client.scrape_url("https://example.com")
        if result.success:
            print(result.markdown)
        client.close()

    Environment variables:
        FIRECRAWL_API_KEY: Required. Your Firecrawl API key.
        FIRECRAWL_API_URL: Optional. Custom API endpoint (default: https://api.firecrawl.dev).
    """

    def __init__(self) -> None:
        self._api_key = os.environ.get("FIRECRAWL_API_KEY", "")
        self._api_url = os.environ.get(
            "FIRECRAWL_API_URL", "https://api.firecrawl.dev"
        ).rstrip("/")
        self._usage = self._load_usage()
        self._last_request_time: float = 0.0
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Lazy-initialize the httpx client."""
        if self._client is None:
            import httpx

            self._client = httpx.Client(
                timeout=60,
                follow_redirects=True,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )
        return self._client

    def scrape_url(
        self,
        url: str,
        *,
        formats: list[str] | None = None,
        wait_for: int = 0,
    ) -> FirecrawlResult:
        """Scrape a single URL via Firecrawl.

        Args:
            url: The URL to scrape.
            formats: Output formats (default: ["markdown"]).
            wait_for: Milliseconds to wait for JS rendering.

        Returns:
            FirecrawlResult with extracted content.
        """
        if not self._api_key:
            return FirecrawlResult(
                url=url,
                success=False,
                error="FIRECRAWL_API_KEY not set",
            )

        if not self._usage.can_fetch():
            return FirecrawlResult(
                url=url,
                success=False,
                error=f"Daily quota exceeded ({MAX_DAILY_FIRECRAWL_PAGES} pages/day)",
            )

        self._rate_limit()

        if formats is None:
            formats = ["markdown"]

        payload: dict = {
            "url": url,
            "formats": formats,
        }
        if wait_for > 0:
            payload["waitFor"] = wait_for

        client = self._get_client()

        for attempt in range(MAX_RETRIES):
            try:
                response = client.post(
                    f"{self._api_url}/v1/scrape",
                    json=payload,
                )

                if response.is_success:
                    data = response.json().get("data", {})
                    self._usage.record_fetch()
                    self._save_usage()

                    return FirecrawlResult(
                        url=url,
                        markdown=data.get("markdown", ""),
                        html=data.get("html", ""),
                        metadata=data.get("metadata", {}),
                        success=True,
                    )

                if response.status_code == 429:
                    # Rate limited — wait and retry
                    wait = min(30 * (2**attempt), 300)
                    logger.warning(
                        "Firecrawl rate limited on %s, waiting %ds", url, wait
                    )
                    time.sleep(wait)
                    continue

                if response.status_code >= 500:
                    # Server error — retry
                    time.sleep(DEFAULT_REQUEST_DELAY * (attempt + 1))
                    continue

                # Client error — don't retry
                return FirecrawlResult(
                    url=url,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                )

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(DEFAULT_REQUEST_DELAY * (attempt + 1))
                    continue
                return FirecrawlResult(
                    url=url,
                    success=False,
                    error=str(e),
                )

        return FirecrawlResult(
            url=url,
            success=False,
            error=f"Failed after {MAX_RETRIES} attempts",
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None
        self._save_usage()

    @property
    def remaining_quota(self) -> int:
        """Return the number of pages remaining in today's quota."""
        return self._usage.remaining

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_usage(self) -> FirecrawlUsage:
        """Load usage data from disk."""
        if _USAGE_FILE.exists():
            try:
                data = json.loads(_USAGE_FILE.read_text(encoding="utf-8"))
                return FirecrawlUsage(
                    date=data.get("date", ""),
                    pages_used=data.get("pages_used", 0),
                )
            except (json.JSONDecodeError, KeyError):
                pass
        return FirecrawlUsage()

    def _save_usage(self) -> None:
        """Persist usage data to disk."""
        try:
            _USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
            _USAGE_FILE.write_text(
                json.dumps(
                    {"date": self._usage.date, "pages_used": self._usage.pages_used},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError:
            logger.debug("Could not save Firecrawl usage file", exc_info=True)

    def _rate_limit(self) -> None:
        """Enforce minimum delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < DEFAULT_REQUEST_DELAY:
            time.sleep(DEFAULT_REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()
