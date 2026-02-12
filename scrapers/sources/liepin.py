"""猎聘网 (Liepin) scraper for discovering Chinese AI companies.

T4 Auxiliary — scrapes 猎聘网 job search pages via Firecrawl (primary)
or httpx+BeautifulSoup (fallback) for AI/ML job listings. Focuses on
mid-to-senior level recruitment, making it a good source for discovering
established AI companies and well-funded startups.

Proxy support: set ``CHINA_PROXY_URL`` environment variable to route
httpx requests through a proxy. Firecrawl uses its own infrastructure.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from scrapers.base_job_scraper import BaseJobSiteScraper, ScrapedCompany
from scrapers.config import SCRAPY_REQUEST_DELAY
from scrapers.utils.china_http import (
    create_china_http_client,
    parse_chinese_job_markdown,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.liepin.com"
_SEARCH_URL = f"{_BASE_URL}/zhaopin/?key={{query}}"


class LiepinScraper(BaseJobSiteScraper):
    """Scrape 猎聘网 for AI/ML job listings to discover Chinese AI companies.

    猎聘网 focuses on mid-to-senior level recruitment. Uses Firecrawl
    when available for better JS-rendered content extraction, falls back
    to direct httpx requests with BeautifulSoup parsing.

    Features:
      - Firecrawl primary (handles JS rendering + anti-bot)
      - httpx + BeautifulSoup fallback
      - User-Agent rotation via china_http utilities
      - Optional proxy support via CHINA_PROXY_URL
      - 7s rate limit delay (slow-and-steady for Chinese sites)
    """

    RATE_LIMIT_DELAY: float = SCRAPY_REQUEST_DELAY

    @property
    def source_name(self) -> str:
        return "liepin"

    def _get_language(self) -> str:
        return "zh"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        """Search 猎聘 for jobs matching keyword."""
        try:
            return self._search_via_firecrawl(keyword, limit)
        except ImportError:
            pass

        return self._search_via_httpx(keyword, limit)

    def _search_via_firecrawl(
        self, keyword: str, limit: int
    ) -> list[dict[str, str]]:
        """Search 猎聘 via Firecrawl for JS-rendered content."""
        from scrapers.utils.firecrawl_client import FirecrawlClient

        fc = FirecrawlClient()
        jobs: list[dict[str, str]] = []

        try:
            if fc.remaining_quota <= 0:
                raise ImportError("Firecrawl quota exhausted")

            url = _SEARCH_URL.format(query=quote(keyword))
            result = fc.scrape_url(url, formats=["markdown"], wait_for=5000)

            if not result.success:
                logger.debug(
                    "liepin Firecrawl failed for '%s': %s", keyword, result.error
                )
                return []

            # Try site-specific markdown parsing first
            jobs = self._parse_liepin_markdown(result.markdown)

            # Fall back to generic Chinese job markdown parser
            if not jobs:
                jobs = parse_chinese_job_markdown(
                    result.markdown, site_name="liepin"
                )

        finally:
            fc.close()

        return jobs[:limit]

    def _search_via_httpx(
        self, keyword: str, limit: int
    ) -> list[dict[str, str]]:
        """Search 猎聘 via direct HTTP request."""
        client = create_china_http_client(referer=f"{_BASE_URL}/")
        jobs: list[dict[str, str]] = []

        try:
            url = _SEARCH_URL.format(query=quote(keyword))
            response = client.get(url)

            if not response.is_success:
                logger.info(
                    "[liepin] HTTP %s for keyword '%s'",
                    response.status_code,
                    keyword,
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

                company_name = (
                    company_el.get_text(strip=True) if company_el else ""
                )
                if not company_name:
                    continue

                jobs.append({
                    "company_name": company_name,
                    "location": (
                        location_el.get_text(strip=True) if location_el else ""
                    ),
                    "job_title": (
                        title_el.get_text(strip=True) if title_el else ""
                    ),
                    "scale": (
                        scale_el.get_text(strip=True) if scale_el else ""
                    ),
                    "industry": (
                        industry_el.get_text(strip=True) if industry_el else ""
                    ),
                })
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.info("[liepin] HTTP error for '%s': %s", keyword, e)
        finally:
            client.close()

        return jobs

    def _parse_liepin_markdown(self, markdown: str) -> list[dict[str, str]]:
        """Parse 猎聘 search results from Firecrawl markdown."""
        jobs: list[dict[str, str]] = []

        # Liepin card pattern:
        #   [Job Title](link) Salary
        #   Company Name  Location  Scale  Industry
        card_pattern = re.compile(
            r"(?:^|\n)"
            r"\[([^\]]{3,60})\]\([^)]*\)"  # [job title](link)
            r"[^\n]{0,40}\n"  # rest of title line (salary etc.)
            r"\s*([^\n·|\-]{2,40})"  # company name
            r"(?:\s*[·|]\s*([^\n·|]{1,20}))?"  # location
            r"(?:\s*[·|]\s*([^\n·|]{1,20}))?"  # scale
            r"(?:\s*[·|]\s*([^\n·|]{1,20}))?",  # industry
            re.MULTILINE,
        )

        for match in card_pattern.finditer(markdown):
            title = match.group(1).strip()
            company = match.group(2).strip()
            location = (match.group(3) or "").strip()
            scale = (match.group(4) or "").strip()
            industry = (match.group(5) or "").strip()

            if not company or len(company) < 2:
                continue

            # Skip navigation elements
            if company in {"猎聘", "首页", "登录", "注册", "搜索", "我的"}:
                continue

            jobs.append({
                "company_name": company,
                "location": location,
                "job_title": title,
                "scale": scale,
                "industry": industry,
            })

        return jobs

    def _extract_company(
        self, job_data: dict[str, str]
    ) -> ScrapedCompany | None:
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
            source_url=_BASE_URL,
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
