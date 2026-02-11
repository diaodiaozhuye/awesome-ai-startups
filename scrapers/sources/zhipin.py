"""Boss直聘 (Zhipin) scraper for discovering Chinese AI companies."""

from __future__ import annotations

import logging
from urllib.parse import quote

from bs4 import BeautifulSoup

from scrapers.base import ScrapedCompany
from scrapers.base_job_scraper import BaseJobSiteScraper
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.zhipin.com/web/geek/job?query={query}&city=100010000"


class ZhipinScraper(BaseJobSiteScraper):
    """Scrape Boss直聘 for AI/ML job listings to discover Chinese AI companies.

    Boss直聘 is one of the largest recruitment platforms in China.
    This scraper uses the public web search pages and extracts company
    information from job listing cards.

    Note: ``city=100010000`` means nationwide (全国).
    """

    RATE_LIMIT_DELAY = 5.0

    @property
    def source_name(self) -> str:
        return "zhipin"

    def _get_language(self) -> str:
        return "zh"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        client = create_http_client()
        # Boss直聘 may check for browser-like headers
        client.headers.update({
            "Referer": "https://www.zhipin.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        jobs: list[dict[str, str]] = []

        try:
            url = _SEARCH_URL.format(query=quote(keyword))
            response = client.get(url)

            if not response.is_success:
                logger.info(
                    "[zhipin] HTTP %s for keyword '%s'", response.status_code, keyword
                )
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(
                ".job-card-wrapper, .job-list li, .search-job-result .job-card"
            )

            for card in cards[:limit]:
                company_el = card.select_one(
                    ".company-name a, .company-name, .info-company .name"
                )
                location_el = card.select_one(
                    ".job-area, .job-area-wrapper .area"
                )
                title_el = card.select_one(
                    ".job-name, .job-title, .info-primary .name"
                )
                scale_el = card.select_one(
                    ".company-tag-list li:last-child, .company-text .scale"
                )
                industry_el = card.select_one(
                    ".company-tag-list li:first-child, .company-text .industry"
                )

                company_name = company_el.get_text(strip=True) if company_el else ""
                if not company_name:
                    continue

                jobs.append({
                    "company_name": company_name,
                    "location": location_el.get_text(strip=True) if location_el else "",
                    "job_title": title_el.get_text(strip=True) if title_el else "",
                    "scale": scale_el.get_text(strip=True) if scale_el else "",
                    "industry": industry_el.get_text(strip=True) if industry_el else "",
                })
        finally:
            client.close()

        return jobs

    def _extract_company(self, job_data: dict[str, str]) -> ScrapedCompany | None:
        name = job_data.get("company_name", "").strip()
        if not name:
            return None

        city = _normalize_city(job_data.get("location", ""))
        category = self._matcher.extract_category(
            job_data.get("job_title", ""), job_data.get("industry", "")
        )
        employee_range = _map_zhipin_scale(job_data.get("scale", ""))

        return ScrapedCompany(
            name=name,
            source="zhipin",
            source_url="https://www.zhipin.com",
            description_zh=job_data.get("industry") or None,
            category=category,
            headquarters_city=city or None,
            headquarters_country="China" if city else None,
            headquarters_country_code="CN" if city else None,
            employee_count_range=employee_range,
            tags=("zhipin",),
            extra={"name_zh": name},
        )


def _normalize_city(raw: str) -> str:
    """Extract the city from a Boss直聘 location string like '北京·朝阳区'."""
    if not raw:
        return ""
    # Split on common separators
    for sep in ("·", "・", "-", " "):
        if sep in raw:
            return raw.split(sep)[0].strip()
    return raw.strip()


_ZHIPIN_SCALE_MAP: dict[str, str] = {
    "0-20人": "1-10",
    "20-99人": "11-50",
    "100-499人": "51-200",
    "500-999人": "501-1000",
    "1000-9999人": "1001-5000",
    "10000人以上": "5001+",
}


def _map_zhipin_scale(raw: str) -> str | None:
    """Map Boss直聘 company scale text to a valid schema employee range."""
    if not raw:
        return None
    raw = raw.strip()
    if raw in _ZHIPIN_SCALE_MAP:
        return _ZHIPIN_SCALE_MAP[raw]
    # Try partial matching
    for key, value in _ZHIPIN_SCALE_MAP.items():
        if key in raw:
            return value
    return None
