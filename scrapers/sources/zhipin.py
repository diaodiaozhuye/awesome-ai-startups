"""Boss直聘 (Zhipin) scraper for discovering Chinese AI companies.

T4 Auxiliary — scrapes Boss直聘 job search pages via Firecrawl (primary)
or httpx+BeautifulSoup (fallback) for AI/ML job listings. Discovers
companies and extracts hiring information including employee scale,
location, and industry.

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

_BASE_URL = "https://www.zhipin.com"
_SEARCH_URL = f"{_BASE_URL}/web/geek/job?query={{query}}&city=100010000"


class ZhipinScraper(BaseJobSiteScraper):
    """Scrape Boss直聘 for AI/ML job listings to discover Chinese AI companies.

    Boss直聘 is one of the largest recruitment platforms in China.
    Uses Firecrawl when available for better JS-rendered content extraction,
    falls back to direct httpx requests with BeautifulSoup parsing.

    Features:
      - Firecrawl primary (handles JS rendering + anti-bot)
      - httpx + BeautifulSoup fallback
      - User-Agent rotation via china_http utilities
      - Optional proxy support via CHINA_PROXY_URL
      - 7s rate limit delay (slow-and-steady for Chinese sites)

    Note: ``city=100010000`` means nationwide (全国).
    """

    RATE_LIMIT_DELAY: float = SCRAPY_REQUEST_DELAY

    @property
    def source_name(self) -> str:
        return "zhipin"

    def _get_language(self) -> str:
        return "zh"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        """Search Boss直聘 for jobs matching keyword."""
        try:
            return self._search_via_firecrawl(keyword, limit)
        except ImportError:
            pass

        return self._search_via_httpx(keyword, limit)

    def _search_via_firecrawl(
        self, keyword: str, limit: int
    ) -> list[dict[str, str]]:
        """Search Boss直聘 via Firecrawl for JS-rendered content."""
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
                    "zhipin Firecrawl failed for '%s': %s", keyword, result.error
                )
                return []

            # Try site-specific markdown parsing first
            jobs = self._parse_zhipin_markdown(result.markdown)

            # Fall back to generic Chinese job markdown parser
            if not jobs:
                jobs = parse_chinese_job_markdown(
                    result.markdown, site_name="zhipin"
                )

        finally:
            fc.close()

        return jobs[:limit]

    def _search_via_httpx(
        self, keyword: str, limit: int
    ) -> list[dict[str, str]]:
        """Search Boss直聘 via direct HTTP request."""
        client = create_china_http_client(referer=f"{_BASE_URL}/")
        jobs: list[dict[str, str]] = []

        try:
            url = _SEARCH_URL.format(query=quote(keyword))
            response = client.get(url)

            if not response.is_success:
                logger.info(
                    "[zhipin] HTTP %s for keyword '%s'",
                    response.status_code,
                    keyword,
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
            logger.info("[zhipin] HTTP error for '%s': %s", keyword, e)
        finally:
            client.close()

        return jobs

    def _parse_zhipin_markdown(self, markdown: str) -> list[dict[str, str]]:
        """Parse Boss直聘 search results from Firecrawl markdown."""
        jobs: list[dict[str, str]] = []

        # Boss直聘 card pattern:
        #   Job Title
        #   Salary
        #   Company · Scale · Industry
        #   Location · Experience · Education
        card_pattern = re.compile(
            r"(?:^|\n)"
            r"\[?([^\]\n]{3,50})\]?"  # job title
            r"(?:\([^)]*\))?\s*\n"
            r"(?:[^\n]{0,30}[kK万]\s*\n)?"  # salary line (optional)
            r"([^\n·]{2,40})"  # company name
            r"(?:\s*[·]\s*([^\n·]{1,20}))?"  # scale
            r"(?:\s*[·]\s*([^\n·]{1,20}))?"  # industry
            r"\s*\n"
            r"([^\n]{2,30})?",  # location
            re.MULTILINE,
        )

        for match in card_pattern.finditer(markdown):
            title = match.group(1).strip()
            company = match.group(2).strip()
            scale = (match.group(3) or "").strip()
            industry = (match.group(4) or "").strip()
            location = (match.group(5) or "").strip()

            if not company or len(company) < 2:
                continue

            # Skip navigation elements
            if company in {"Boss直聘", "首页", "登录", "注册", "搜索"}:
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
        employee_range = _map_zhipin_scale(job_data.get("scale", ""))

        return ScrapedCompany(
            name=name,
            source="zhipin",
            source_url=_BASE_URL,
            description_zh=job_data.get("industry") or None,
            category=category,
            company_headquarters_city=city or None,
            company_headquarters_country="China" if city else None,
            company_headquarters_country_code="CN" if city else None,
            company_employee_count_range=employee_range,
            tags=("zhipin",),
            extra={"name_zh": name},
        )


def _normalize_city(raw: str) -> str:
    """Extract the city from a Boss直聘 location string like '北京·朝阳区'."""
    if not raw:
        return ""
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
    for key, value in _ZHIPIN_SCALE_MAP.items():
        if key in raw:
            return value
    return None
