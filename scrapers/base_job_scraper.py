"""Abstract base class for job-site scrapers.

Job-site scrapers discover AI companies by searching recruitment platforms
for AI/ML job titles, then extracting company information from the listings.
This module provides the shared orchestration logic (keyword iteration,
rate limiting, within-scraper deduplication) so that concrete scrapers only
need to implement site-specific HTTP requests and HTML parsing.
"""

from __future__ import annotations

import logging
import time
from abc import abstractmethod
from dataclasses import fields, replace
from typing import Any

from scrapers.base import BaseScraper, ScrapedCompany
from scrapers.config import JOB_SCRAPER_MAX_JOBS_PER_KEYWORD, JOB_SCRAPER_RATE_LIMIT
from scrapers.keyword_matcher import JobKeywordMatcher
from scrapers.utils import extract_domain

logger = logging.getLogger(__name__)


class BaseJobSiteScraper(BaseScraper):
    """Template-method base class for all job-site scrapers.

    Subclasses must implement:
      - ``source_name`` property
      - ``_search_jobs(keyword, limit)`` — site-specific job search
      - ``_extract_company(job_data)`` — extract a ScrapedCompany from one job listing

    The ``scrape()`` method orchestrates: iterate keywords → search → extract
    → deduplicate companies from multiple listings.
    """

    RATE_LIMIT_DELAY: float = JOB_SCRAPER_RATE_LIMIT
    MAX_JOBS_PER_KEYWORD: int = JOB_SCRAPER_MAX_JOBS_PER_KEYWORD

    def __init__(self) -> None:
        self._matcher = JobKeywordMatcher()
        self._last_request_time: float = 0.0

    # ------------------------------------------------------------------
    # Abstract methods for subclasses
    # ------------------------------------------------------------------

    @abstractmethod
    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        """Search the job site for listings matching *keyword*.

        Returns a list of dicts whose structure is scraper-specific.
        Each dict should contain enough information for ``_extract_company``
        to build a :class:`ScrapedCompany`.
        """
        ...

    @abstractmethod
    def _extract_company(self, job_data: dict[str, str]) -> ScrapedCompany | None:
        """Extract company information from a single job listing.

        Return ``None`` if the listing doesn't contain enough data.
        """
        ...

    # ------------------------------------------------------------------
    # Template method
    # ------------------------------------------------------------------

    def scrape(self, limit: int = 100) -> list[ScrapedCompany]:
        """Scrape AI companies by searching jobs and deduplicating results."""
        keywords = self._matcher.get_search_keywords(self._get_language())
        seen: dict[str, ScrapedCompany] = {}  # dedup key → company

        for keyword in keywords:
            if len(seen) >= limit:
                break

            self._rate_limit()

            try:
                jobs = self._search_jobs(keyword, self.MAX_JOBS_PER_KEYWORD)
            except Exception:
                logger.warning(
                    "[%s] Error searching '%s'",
                    self.source_name,
                    keyword,
                    exc_info=True,
                )
                continue

            for job in jobs:
                company = self._extract_company(job)
                if company is None:
                    continue

                key = self._dedup_key(company)
                if key in seen:
                    seen[key] = self._merge(seen[key], company)
                else:
                    seen[key] = company

                if len(seen) >= limit:
                    break

        return list(seen.values())[:limit]

    # ------------------------------------------------------------------
    # Hooks (override in subclass if needed)
    # ------------------------------------------------------------------

    def _get_language(self) -> str:
        """Return the language code for keyword search (``"en"`` or ``"zh"``)."""
        return "en"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Sleep if necessary to respect the rate limit between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    @staticmethod
    def _dedup_key(company: ScrapedCompany) -> str:
        """Generate a deduplication key from domain or lowercased name."""
        if company.website:
            domain = extract_domain(company.website)
            if domain:
                return domain
        return company.name.lower().strip()

    @staticmethod
    def _merge(existing: ScrapedCompany, incoming: ScrapedCompany) -> ScrapedCompany:
        """Merge data from a duplicate listing into the existing record.

        Strategy: keep ``name`` and ``source`` from *existing*; for all other
        fields, prefer the non-empty / non-None value.  Tags are unioned.
        """
        updates: dict[str, Any] = {}
        keep_fields = {"name", "source", "source_url"}

        for f in fields(existing):
            if f.name in keep_fields:
                continue

            old = getattr(existing, f.name)
            new = getattr(incoming, f.name)

            if f.name == "tags":
                merged_tags = tuple(dict.fromkeys((*existing.tags, *incoming.tags)))
                if merged_tags != existing.tags:
                    updates["tags"] = merged_tags
            elif not old and new:
                updates[f.name] = new

        return replace(existing, **updates) if updates else existing
