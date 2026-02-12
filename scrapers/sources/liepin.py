"""猎聘网 (Liepin) scraper for discovering Chinese AI companies."""

from __future__ import annotations

import logging
from urllib.parse import quote

from bs4 import BeautifulSoup

from scrapers.base import ScrapedProduct
from scrapers.base_job_scraper import BaseJobSiteScraper
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.liepin.com/zhaopin/?key={query}"


class LiepinScraper(BaseJobSiteScraper):
    """Scrape 猎聘网 for AI/ML job listings to discover Chinese AI companies.

    猎聘网 focuses on mid-to-senior level recruitment, making it a good
    source for discovering established AI companies and well-funded startups.
    """

    RATE_LIMIT_DELAY = 5.0

    @property
    def source_name(self) -> str:
        return "liepin"

    def _get_language(self) -> str:
        return "zh"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        client = create_http_client()
        client.headers.update({
            "Referer": "https://www.liepin.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        jobs: list[dict[str, str]] = []

        try:
            url = _SEARCH_URL.format(query=quote(keyword))
            response = client.get(url)

            if not response.is_success:
                logger.info(
                    "[liepin] HTTP %s for keyword '%s'", response.status_code, keyword
                )
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(
                ".job-list-item, .sojob-item-main, "
                ".job-card, .content-left-section .job-info"
            )

            for card in cards[:limit]:
                company_el = card.select_one(
                    ".company-name a, .company-name, .recruit-name"
                )
                location_el = card.select_one(
                    ".job-dq, .address, .recruit-address"
                )
                title_el = card.select_one(
                    ".job-title a, .job-title, .recruit-title"
                )
                scale_el = card.select_one(
                    ".company-info .scale, .company-tag:last-child"
                )
                industry_el = card.select_one(
                    ".company-info .industry, .company-tag:first-child"
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
        employee_range = _map_liepin_scale(job_data.get("scale", ""))

        return ScrapedCompany(
            name=name,
            source="liepin",
            source_url="https://www.liepin.com",
            description_zh=job_data.get("industry") or None,
            category=category,
            company_headquarters_city=city or None,
            company_headquarters_country="China" if city else None,
            company_headquarters_country_code="CN" if city else None,
            company_employee_count_range=employee_range,
            tags=("liepin",),
            extra={"name_zh": name},
        )


def _normalize_city(raw: str) -> str:
    """Extract the city from a Liepin location like '北京-朝阳区'."""
    if not raw:
        return ""
    for sep in ("-", "·", "・", " "):
        if sep in raw:
            return raw.split(sep)[0].strip()
    return raw.strip()


_LIEPIN_SCALE_MAP: dict[str, str] = {
    "1-49人": "11-50",
    "50-99人": "51-200",
    "100-499人": "51-200",
    "500-999人": "501-1000",
    "1000-9999人": "1001-5000",
    "10000人以上": "5001+",
    "10000+": "5001+",
}


def _map_liepin_scale(raw: str) -> str | None:
    """Map 猎聘 company scale text to a valid schema employee range."""
    if not raw:
        return None
    raw = raw.strip()
    if raw in _LIEPIN_SCALE_MAP:
        return _LIEPIN_SCALE_MAP[raw]
    for key, value in _LIEPIN_SCALE_MAP.items():
        if key in raw:
            return value
    return None
