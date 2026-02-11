"""TechCrunch RSS feed scraper stub.

This is a stub implementation. Full version would parse TechCrunch's
AI category RSS feed for newly mentioned companies.
"""

from __future__ import annotations

from scrapers.base import BaseScraper, ScrapedCompany


class TechCrunchScraper(BaseScraper):
    """Stub scraper for TechCrunch RSS feeds.

    Would parse:
    - https://techcrunch.com/category/artificial-intelligence/feed/
    """

    @property
    def source_name(self) -> str:
        return "techcrunch"

    def scrape(self, limit: int = 100) -> list[ScrapedCompany]:
        print(
            f"[TechCrunch] Stub: not yet implemented. Would fetch up to {limit} companies."
        )
        return []
