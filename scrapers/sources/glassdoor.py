"""Glassdoor job search scraper for discovering AI companies."""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scrapers.base import ScrapedCompany
from scrapers.base_job_scraper import BaseJobSiteScraper
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query}"


class GlassdoorScraper(BaseJobSiteScraper):
    """Scrape Glassdoor public job search results for AI company information.

    Glassdoor provides company name, location, and sometimes employee count
    in its job listing pages.
    """

    RATE_LIMIT_DELAY = 5.0

    @property
    def source_name(self) -> str:
        return "glassdoor"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        client = create_http_client()
        jobs: list[dict[str, str]] = []

        try:
            url = _SEARCH_URL.format(query=quote_plus(keyword))
            response = client.get(url)

            if not response.is_success:
                logger.info(
                    "[glassdoor] HTTP %s for keyword '%s'",
                    response.status_code,
                    keyword,
                )
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(
                "li.react-job-listing, "
                "[data-test='jobListing'], "
                ".jobCard, "
                "article.job-listing"
            )

            for card in cards[:limit]:
                name_el = card.select_one(
                    ".job-search-key-l2wjgv, "
                    "[data-test='emp-name'], "
                    ".employerName, "
                    ".company-name"
                )
                location_el = card.select_one(
                    "[data-test='emp-location'], .location, .job-location"
                )
                title_el = card.select_one(
                    "[data-test='job-title'], .jobTitle, .job-title"
                )
                size_el = card.select_one(".companySize, .employer-size")

                company_name = name_el.get_text(strip=True) if name_el else ""
                if not company_name:
                    continue

                jobs.append(
                    {
                        "company_name": company_name,
                        "location": (
                            location_el.get_text(strip=True) if location_el else ""
                        ),
                        "job_title": title_el.get_text(strip=True) if title_el else "",
                        "employee_count": (
                            size_el.get_text(strip=True) if size_el else ""
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

        category = self._matcher.extract_category(job_data.get("job_title", ""))
        employee_range = _normalize_employee_count(job_data.get("employee_count", ""))

        return ScrapedCompany(
            name=name,
            source="glassdoor",
            source_url="https://www.glassdoor.com",
            category=category,
            company_headquarters_city=city or None,
            company_headquarters_country=country or None,
            company_employee_count_range=employee_range,
            tags=("glassdoor",),
        )


def _parse_location(location: str) -> tuple[str, str]:
    """Parse a Glassdoor location string."""
    if not location:
        return ("", "")
    parts = [p.strip() for p in location.split(",")]
    city = parts[0] if parts else ""
    country = parts[-1] if len(parts) >= 2 else ""
    return (city, country)


_EMPLOYEE_RANGES = {
    "1-10",
    "11-50",
    "51-200",
    "201-500",
    "501-1000",
    "1001-5000",
    "5001+",
}


def _normalize_employee_count(raw: str) -> str | None:
    """Map a raw employee count string to a valid schema range."""
    if not raw:
        return None
    raw = raw.strip().replace(" ", "").replace(",", "")
    if raw in _EMPLOYEE_RANGES:
        return raw
    # Try to extract a number and map to the closest range
    digits = "".join(c for c in raw if c.isdigit())
    if not digits:
        return None
    count = int(digits)
    if count <= 10:
        return "1-10"
    if count <= 50:
        return "11-50"
    if count <= 200:
        return "51-200"
    if count <= 500:
        return "201-500"
    if count <= 1000:
        return "501-1000"
    if count <= 5000:
        return "1001-5000"
    return "5001+"
