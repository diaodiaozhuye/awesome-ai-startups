"""Indeed job board scraper for discovering AI companies.

T4 Auxiliary — scrapes Indeed job search pages via Firecrawl
for AI/ML job listings to discover companies and extract
hiring information.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

from scrapers.base_job_scraper import BaseJobSiteScraper, ScrapedCompany
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.indeed.com/jobs?q={query}&fromage=30&limit=20&start={start}"

# AI-related job search keywords
_SEARCH_KEYWORDS = [
    "AI engineer",
    "machine learning engineer",
    "deep learning",
    "LLM engineer",
    "NLP engineer",
    "computer vision engineer",
    "AI researcher",
    "ML infrastructure",
    "AI product manager",
    "generative AI",
    "MLOps engineer",
    "AI safety",
]


class IndeedScraper(BaseJobSiteScraper):
    """Scrape Indeed for AI/ML job listings to discover companies.

    Uses Firecrawl when available for better HTML extraction,
    falls back to direct httpx requests with BeautifulSoup parsing.
    """

    RATE_LIMIT_DELAY = 5.0

    @property
    def source_name(self) -> str:
        return "indeed"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        """Search Indeed for jobs matching keyword."""
        # Try Firecrawl first for better extraction
        try:
            return self._search_via_firecrawl(keyword, limit)
        except ImportError:
            pass

        # Fallback to direct HTTP
        return self._search_via_httpx(keyword, limit)

    def _search_via_firecrawl(self, keyword: str, limit: int) -> list[dict[str, str]]:
        """Search Indeed via Firecrawl for JS-rendered content."""
        from scrapers.utils.firecrawl_client import FirecrawlClient

        fc = FirecrawlClient()
        jobs: list[dict[str, str]] = []

        try:
            if fc.remaining_quota <= 0:
                raise ImportError("Firecrawl quota exhausted")

            url = _SEARCH_URL.format(query=quote_plus(keyword), start=0)
            result = fc.scrape_url(url, formats=["markdown"], wait_for=3000)

            if not result.success:
                logger.debug(
                    "Indeed Firecrawl failed for '%s': %s", keyword, result.error
                )
                return []

            jobs = self._parse_indeed_markdown(result.markdown)

        finally:
            fc.close()

        return jobs[:limit]

    def _search_via_httpx(self, keyword: str, limit: int) -> list[dict[str, str]]:
        """Search Indeed via direct HTTP request."""
        from bs4 import BeautifulSoup

        client = create_http_client()
        client.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
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

    def _parse_indeed_markdown(self, markdown: str) -> list[dict[str, str]]:
        """Parse Indeed search results from Firecrawl markdown output."""
        jobs: list[dict[str, str]] = []

        # Pattern: job card with company name, title, location
        card_pattern = re.compile(
            r"(?:^|\n)"
            r"(?:#{1,4}\s+)?"
            r"\[?([^\]\n]{3,80})\]?"  # job title
            r"(?:\([^)]*\))?\s*\n"
            r"([^\n]{2,60})\s*"  # company name
            r"(?:[-–—|]\s*([^\n]{2,60}))?"  # location
            r"\s*\n"
            r"([^\n]{10,500})?",  # snippet
            re.MULTILINE,
        )

        for match in card_pattern.finditer(markdown):
            job_title = match.group(1).strip()
            company_name = match.group(2).strip()
            location = (match.group(3) or "").strip()
            snippet = (match.group(4) or "").strip()

            if not company_name or len(company_name) < 2:
                continue

            # Skip navigation elements
            if company_name.lower() in {
                "indeed",
                "sign in",
                "post",
                "resume",
                "salary",
                "company",
            }:
                continue

            jobs.append(
                {
                    "company_name": company_name,
                    "location": location,
                    "job_title": job_title,
                    "snippet": snippet,
                }
            )

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
    region = parts[1] if len(parts) > 1 else ""
    if len(region) == 2 and region.isalpha():
        return (city, "United States")
    return (city, region)
