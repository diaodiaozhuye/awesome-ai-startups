"""LinkedIn public job search scraper for discovering AI companies."""

from __future__ import annotations

import logging
import random
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scrapers.base import ScrapedCompany
from scrapers.base_job_scraper import BaseJobSiteScraper
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_SEARCH_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    "?keywords={query}&start={start}"
)

_USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
]


class LinkedInJobsScraper(BaseJobSiteScraper):
    """Scrape LinkedIn's public job search pages (no authentication required).

    Uses the guest jobs API endpoint which returns HTML fragments.
    Rotates User-Agent headers and uses conservative rate limiting
    to reduce the risk of being blocked.
    """

    RATE_LIMIT_DELAY = 5.0

    @property
    def source_name(self) -> str:
        return "linkedin-jobs"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        client = create_http_client()
        client.headers["User-Agent"] = random.choice(_USER_AGENTS)  # noqa: S311
        jobs: list[dict[str, str]] = []

        try:
            url = _SEARCH_URL.format(query=quote_plus(keyword), start=0)
            response = client.get(url)

            if not response.is_success:
                logger.info(
                    "[linkedin-jobs] HTTP %s for keyword '%s'",
                    response.status_code,
                    keyword,
                )
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select("li, div.base-card, div.job-search-card")

            for card in cards[:limit]:
                name_el = card.select_one(
                    "h4.base-search-card__subtitle, .base-search-card__subtitle a"
                )
                location_el = card.select_one(
                    ".job-search-card__location, .base-search-card__metadata"
                )
                title_el = card.select_one(
                    "h3.base-search-card__title, .base-search-card__title"
                )
                link_el = card.select_one(
                    "a.base-card__full-link, a[href*='/company/']"
                )

                company_name = name_el.get_text(strip=True) if name_el else ""
                if not company_name:
                    continue

                linkedin_url = ""
                if link_el:
                    href = str(link_el.get("href", ""))
                    if "/company/" in href:
                        linkedin_url = href.split("?")[0]

                jobs.append(
                    {
                        "company_name": company_name,
                        "location": (
                            location_el.get_text(strip=True) if location_el else ""
                        ),
                        "job_title": title_el.get_text(strip=True) if title_el else "",
                        "linkedin_url": linkedin_url,
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

        category = self._matcher.extract_category(job_data.get("job_title", ""))

        return ScrapedCompany(
            name=name,
            source="linkedin-jobs",
            source_url="https://www.linkedin.com/jobs",
            category=category,
            headquarters_city=city or None,
            headquarters_country=country or None,
            linkedin_url=job_data.get("linkedin_url") or None,
            tags=("linkedin",),
        )


def _parse_location(location: str) -> tuple[str, str]:
    """Parse a LinkedIn location like 'San Francisco, CA, United States'."""
    if not location:
        return ("", "")
    parts = [p.strip() for p in location.split(",")]
    city = parts[0] if parts else ""
    country = parts[-1] if len(parts) >= 2 else ""
    return (city, country)
