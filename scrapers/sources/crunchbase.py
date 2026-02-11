"""Crunchbase API scraper stub.

This is a stub implementation. To fully implement, you need a Crunchbase
Basic API key (free tier: 200 requests/day).
"""

from __future__ import annotations

from scrapers.base import BaseScraper, ScrapedCompany


class CrunchbaseScraper(BaseScraper):
    """Stub scraper for Crunchbase.

    Requires: CRUNCHBASE_API_KEY env var.
    Full implementation would query their Organization Search API
    filtering for AI/ML categories.
    """

    @property
    def source_name(self) -> str:
        return "crunchbase"

    def scrape(self, limit: int = 100) -> list[ScrapedCompany]:
        print(
            f"[Crunchbase] Stub: not yet implemented. Would fetch up to {limit} companies."
        )
        return []
