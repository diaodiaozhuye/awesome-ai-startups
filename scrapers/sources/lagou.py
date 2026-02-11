"""拉勾网 (Lagou) scraper for discovering Chinese AI companies."""

from __future__ import annotations

import logging
from urllib.parse import quote

from bs4 import BeautifulSoup

from scrapers.base import ScrapedCompany
from scrapers.base_job_scraper import BaseJobSiteScraper
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.lagou.com/zhaopin/{query}/"


class LagouScraper(BaseJobSiteScraper):
    """Scrape 拉勾网 for AI/ML job listings to discover Chinese tech companies.

    拉勾网 is a popular Chinese tech-focused recruitment platform,
    particularly strong for internet and startup companies.
    """

    RATE_LIMIT_DELAY = 5.0

    @property
    def source_name(self) -> str:
        return "lagou"

    def _get_language(self) -> str:
        return "zh"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        client = create_http_client()
        client.headers.update({
            "Referer": "https://www.lagou.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        jobs: list[dict[str, str]] = []

        try:
            url = _SEARCH_URL.format(query=quote(keyword))
            response = client.get(url)

            if not response.is_success:
                logger.info(
                    "[lagou] HTTP %s for keyword '%s'", response.status_code, keyword
                )
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(
                ".item__10RTO, .con_list_item, "
                ".position-list li, .s_position_list li"
            )

            for card in cards[:limit]:
                company_el = card.select_one(
                    ".company_name a, .company-name, .company__2J6hC"
                )
                location_el = card.select_one(
                    ".add em, .position-address, .city__2EZWN"
                )
                title_el = card.select_one(
                    ".p_top h3, .position_link h3, .name__3gHTl"
                )
                scale_el = card.select_one(
                    ".industry li:last-child, .scale, .size__3hIJq"
                )
                industry_el = card.select_one(
                    ".industry li:first-child, .industry__1HBos"
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

        city = job_data.get("location", "").strip()
        category = self._matcher.extract_category(
            job_data.get("job_title", ""), job_data.get("industry", "")
        )
        employee_range = _map_lagou_scale(job_data.get("scale", ""))

        return ScrapedCompany(
            name=name,
            source="lagou",
            source_url="https://www.lagou.com",
            description_zh=job_data.get("industry") or None,
            category=category,
            headquarters_city=city or None,
            headquarters_country="China" if city else None,
            headquarters_country_code="CN" if city else None,
            employee_count_range=employee_range,
            tags=("lagou",),
            extra={"name_zh": name},
        )


_LAGOU_SCALE_MAP: dict[str, str] = {
    "少于15人": "1-10",
    "15-50人": "11-50",
    "50-150人": "51-200",
    "150-500人": "201-500",
    "500-2000人": "501-1000",
    "2000人以上": "5001+",
}


def _map_lagou_scale(raw: str) -> str | None:
    """Map 拉勾 company scale text to a valid schema employee range."""
    if not raw:
        return None
    raw = raw.strip()
    if raw in _LAGOU_SCALE_MAP:
        return _LAGOU_SCALE_MAP[raw]
    for key, value in _LAGOU_SCALE_MAP.items():
        if key in raw:
            return value
    return None
