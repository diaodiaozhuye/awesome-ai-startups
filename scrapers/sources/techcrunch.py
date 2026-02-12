"""TechCrunch RSS feed scraper stub.

This is a stub implementation. Full version will use Firecrawl
to parse TechCrunch's AI category for funding news.
"""

from __future__ import annotations

import logging

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier

logger = logging.getLogger(__name__)


class TechCrunchScraper(BaseScraper):
    """Stub scraper for TechCrunch RSS feeds.

    Full implementation (Phase 4) will use Firecrawl to scrape
    TechCrunch AI category pages for funding news.
    """

    @property
    def source_name(self) -> str:
        return "techcrunch"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        logger.info("TechCrunch stub: not yet implemented (Phase 4).")
        return []
