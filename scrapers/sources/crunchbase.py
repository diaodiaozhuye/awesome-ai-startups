"""Crunchbase API scraper stub.

This is a stub implementation. Full version will use Firecrawl
to scrape Crunchbase web pages for funding data.
"""

from __future__ import annotations

import logging

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier

logger = logging.getLogger(__name__)


class CrunchbaseScraper(BaseScraper):
    """Stub scraper for Crunchbase.

    Full implementation (Phase 2) will use Firecrawl to scrape
    Crunchbase organization pages for funding and company data.
    """

    @property
    def source_name(self) -> str:
        return "crunchbase"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T1_AUTHORITATIVE

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        logger.info("Crunchbase stub: not yet implemented (Phase 2).")
        return []
