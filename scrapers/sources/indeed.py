"""Indeed job board scraper for discovering AI companies."""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scrapers.base_job_scraper import BaseJobSiteScraper
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.indeed.com/jobs?q={query}&fromage=30&limit=20&start={start}"


class IndeedScraper(BaseJobSiteScraper):
    """Scrape Indeed for AI/ML job listings to discover companies.

    Uses the public Indeed job search pages (no API key required).
    Extracts company name, location, and description from job cards.
    """

    RATE_LIMIT_DELAY = 3.0

    @property
    def source_name(self) -> str:
        return "indeed"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        client = create_http_client()
        client.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            }
        )
        jobs: list[dict[str, str]] = []

        try:
            url = _SEARCH_URL.format(query=quote_plus(keyword), start=0)
            response = client.get(url)
            if not response.is_success:
                logger.info("[indeed] HTTP %s for '%s'", response.status_code, keyword)
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select("div.job_seen_beacon, div.jobsearch-ResultsList > div")

            for card in cards[:limit]:
                company_el = card.select_one(
                    "[data-testid='company-name'], .companyName, .company"
                )
                location_el = card.select_one(
                    "[data-testid='text-location'], .companyLocation, .location"
                )
                title_el = card.select_one(
                    "h2.jobTitle a, .jobTitle > a, a.jcs-JobTitle"
                )
                snippet_el = card.select_one(
                    ".job-snippet, .jobsearch-JobComponent-description"
                )

                company_name = company_el.get_text(strip=True) if company_el else ""
                if not company_name:
                    continue

                jobs.append(
                    {
                        "company_name": company_name,
                        "location": (
                            location_el.get_text(strip=True) if location_el else ""
                        ),
                        "job_title": title_el.get_text(strip=True) if title_el else "",
                        "snippet": (
                            snippet_el.get_text(strip=True) if snippet_el else ""
                        ),
                    }
                )
        finally:
            client.close()

        return jobs

    def _extract_company(self, job_data: dict[str, str]) -> ScrapedCompany | None:
        name = job_data.get("company_name", "").strip()
        if not name:
            return None

        location = job_data.get("location", "")
        city, country = _parse_location(location)

        category = self._matcher.extract_category(
            job_data.get("job_title", ""), job_data.get("snippet", "")
        )

        return ScrapedCompany(
            name=name,
            source="indeed",
            source_url="https://www.indeed.com",
            description=job_data.get("snippet") or None,
            category=category,
            company_headquarters_city=city or None,
            company_headquarters_country=country or None,
            tags=("indeed",),
        )


def _parse_location(location: str) -> tuple[str, str]:
    """Parse an Indeed location string like 'San Francisco, CA' into (city, country)."""
    if not location:
        return ("", "")
    parts = [p.strip() for p in location.split(",")]
    city = parts[0] if parts else ""
    # Indeed US locations use state abbreviations; international may have country
    region = parts[1] if len(parts) > 1 else ""
    # Heuristic: 2-letter codes are US states
    if len(region) == 2 and region.isalpha():
        return (city, "United States")
    return (city, region)
