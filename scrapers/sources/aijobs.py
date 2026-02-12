"""AI-Jobs.net scraper for discovering AI companies."""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup, Tag

from scrapers.base_job_scraper import BaseJobSiteScraper
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_BASE_URL = "https://ai-jobs.net"


class AIJobsScraper(BaseJobSiteScraper):
    """Scrape AI-Jobs.net for company information.

    Since AI-Jobs.net is an AI-specific job board, all listings are
    relevant — no keyword filtering needed.  We override ``scrape()``
    directly to crawl the listing pages.
    """

    RATE_LIMIT_DELAY = 2.0

    @property
    def source_name(self) -> str:
        return "aijobs"

    def scrape(self, limit: int = 100) -> list[ScrapedCompany]:
        """Scrape the AI-Jobs.net listing pages directly."""
        client = create_http_client()
        seen: dict[str, ScrapedCompany] = {}

        try:
            page = 1
            while len(seen) < limit:
                self._rate_limit()
                url = f"{_BASE_URL}/?page={page}" if page > 1 else _BASE_URL
                response = client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.select(
                    "article.job, .job-listing, tr.job-row, div.job-card"
                )

                if not cards:
                    # Also try a broader selector for the listing table
                    cards = soup.select(
                        "table tbody tr, .jobs-list > div, ul.jobs > li"
                    )

                if not cards:
                    break

                for card in cards:
                    company = self._parse_card(card)
                    if company is None:
                        continue

                    key = self._dedup_key(company)
                    if key not in seen:
                        seen[key] = company
                    else:
                        seen[key] = self._merge(seen[key], company)

                    if len(seen) >= limit:
                        break

                page += 1
                if page > 10:
                    break
        finally:
            client.close()

        return list(seen.values())[:limit]

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        # Not used — scrape() is overridden.
        return []  # pragma: no cover

    def _extract_company(self, job_data: dict[str, str]) -> ScrapedCompany | None:
        # Not used — scrape() is overridden.
        return None  # pragma: no cover

    def _parse_card(self, card: Tag) -> ScrapedCompany | None:
        """Extract company info from a single job card element."""
        company_el = card.select_one(".company, .company-name, td:nth-child(2)")
        location_el = card.select_one(".location, .job-location, td:nth-child(3)")
        link_el = card.select_one("a[href]")

        name = company_el.get_text(strip=True) if company_el else ""
        if not name:
            # Fallback: try to get text from the second column or a specific element
            all_text = card.get_text(" ", strip=True)
            if not all_text:
                return None
            name = all_text.split("|")[0].strip() if "|" in all_text else ""
            if not name:
                return None

        location = location_el.get_text(strip=True) if location_el else ""
        source_url = _BASE_URL
        if link_el and link_el.get("href"):
            href = str(link_el["href"])
            if href.startswith("/"):
                source_url = f"{_BASE_URL}{href}"
            elif href.startswith("http"):
                source_url = href

        return ScrapedCompany(
            name=name,
            source="aijobs",
            source_url=source_url,
            company_headquarters_city=(
                location.split(",")[0].strip() if location else None
            ),
            company_headquarters_country=(
                location.split(",")[-1].strip() if "," in location else None
            ),
            tags=("aijobs",),
        )
