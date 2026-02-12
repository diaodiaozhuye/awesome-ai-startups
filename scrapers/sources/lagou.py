"""拉勾网 (Lagou) scraper for discovering Chinese AI companies.

T4 Auxiliary — scrapes 拉勾网 job search pages via Firecrawl (primary)
or httpx+BeautifulSoup (fallback) for AI/ML job listings. 拉勾 is a
popular Chinese tech-focused recruitment platform, particularly strong
for internet and startup companies.

Proxy support: set ``CHINA_PROXY_URL`` environment variable to route
httpx requests through a proxy. Firecrawl uses its own infrastructure.

Note: 拉勾 has the strongest anti-scraping measures among Chinese job
sites. Firecrawl is strongly recommended for this source.
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

_BASE_URL = "https://www.lagou.com"
_SEARCH_URL = f"{_BASE_URL}/zhaopin/{{query}}/"

# Lagou has the strongest anti-bot protection; use even higher delay
_LAGOU_RATE_LIMIT_DELAY = max(SCRAPY_REQUEST_DELAY, 10.0)


class LagouScraper(BaseJobSiteScraper):
    """Scrape 拉勾网 for AI/ML job listings to discover Chinese tech companies.

    拉勾 has the strongest anti-scraping measures among the three Chinese
    job sites. Firecrawl is strongly recommended. Falls back to httpx
    with enhanced anti-detection headers.

    Features:
      - Firecrawl primary (strongly recommended for 拉勾)
      - httpx + BeautifulSoup fallback (may get blocked)
      - User-Agent rotation via china_http utilities
      - Optional proxy support via CHINA_PROXY_URL
      - 10s rate limit delay (highest among Chinese sites)
    """

    RATE_LIMIT_DELAY: float = _LAGOU_RATE_LIMIT_DELAY

    @property
    def source_name(self) -> str:
        return "lagou"

    def _get_language(self) -> str:
        return "zh"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        """Search 拉勾 for jobs matching keyword."""
        try:
            return self._search_via_firecrawl(keyword, limit)
        except ImportError:
            pass

        return self._search_via_httpx(keyword, limit)

    def _search_via_firecrawl(
        self, keyword: str, limit: int
    ) -> list[dict[str, str]]:
        """Search 拉勾 via Firecrawl for JS-rendered content."""
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
                    "lagou Firecrawl failed for '%s': %s", keyword, result.error
                )
                return []

            # Try site-specific markdown parsing first
            jobs = self._parse_lagou_markdown(result.markdown)

            # Fall back to generic Chinese job markdown parser
            if not jobs:
                jobs = parse_chinese_job_markdown(
                    result.markdown, site_name="lagou"
                )

        finally:
            fc.close()

        return jobs[:limit]

    def _search_via_httpx(
        self, keyword: str, limit: int
    ) -> list[dict[str, str]]:
        """Search 拉勾 via direct HTTP request.

        Note: 拉勾 has strong anti-bot protection, so this fallback
        may not always succeed. Firecrawl is recommended.
        """
        client = create_china_http_client(referer=f"{_BASE_URL}/")
        jobs: list[dict[str, str]] = []

        try:
            url = _SEARCH_URL.format(query=quote(keyword))
            response = client.get(url)

            if not response.is_success:
                logger.info(
                    "[lagou] HTTP %s for keyword '%s'",
                    response.status_code,
                    keyword,
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
            logger.info("[lagou] HTTP error for '%s': %s", keyword, e)
        finally:
            client.close()

        return jobs

    def _parse_lagou_markdown(self, markdown: str) -> list[dict[str, str]]:
        """Parse 拉勾 search results from Firecrawl markdown."""
        jobs: list[dict[str, str]] = []

        # Lagou card pattern (React-based, class names are hashed):
        #   Job Title  Salary  Location
        #   Company · Scale · Industry · Funding Stage
        card_pattern = re.compile(
            r"(?:^|\n)"
            r"\[?([^\]\n]{3,50})\]?"  # job title
            r"[^\n]{0,50}\n"  # salary, experience, etc.
            r"\s*([^\n·|\-]{2,40})"  # company name
            r"(?:\s*[·|/]\s*([^\n·|/]{1,20}))?"  # scale or industry
            r"(?:\s*[·|/]\s*([^\n·|/]{1,20}))?"  # industry or funding
            r"(?:\s*[·|/]\s*([^\n·|/]{1,20}))?",  # funding stage
            re.MULTILINE,
        )

        for match in card_pattern.finditer(markdown):
            title = match.group(1).strip()
            company = match.group(2).strip()
            field3 = (match.group(3) or "").strip()
            field4 = (match.group(4) or "").strip()
            field5 = (match.group(5) or "").strip()

            if not company or len(company) < 2:
                continue

            # Skip navigation elements
            if company in {"拉勾", "首页", "登录", "注册", "搜索", "职位"}:
                continue

            # Heuristic: determine which field is scale vs industry
            scale = ""
            industry = ""
            for f in (field3, field4, field5):
                if not f:
                    continue
                if _looks_like_scale(f):
                    scale = f
                elif not industry:
                    industry = f

            jobs.append({
                "company_name": company,
                "location": "",
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

        city = job_data.get("location", "").strip()
        category = self._matcher.extract_category(
            job_data.get("job_title", ""), job_data.get("industry", "")
        )
        employee_range = _map_lagou_scale(job_data.get("scale", ""))

        return ScrapedCompany(
            name=name,
            source="lagou",
            source_url=_BASE_URL,
            description_zh=job_data.get("industry") or None,
            category=category,
            company_headquarters_city=city or None,
            company_headquarters_country="China" if city else None,
            company_headquarters_country_code="CN" if city else None,
            company_employee_count_range=employee_range,
            tags=("lagou",),
            extra={"name_zh": name},
        )


_SCALE_PATTERN = re.compile(r"\d+[-~]\d+人|\d+人以上|\d+\+")


def _looks_like_scale(text: str) -> bool:
    """Heuristic: does this text look like a company scale string?"""
    return bool(_SCALE_PATTERN.search(text))


_LAGOU_SCALE_MAP: dict[str, str] = {
    "少于15人": "1-10",
    "15-50人": "11-50",
    "50-150人": "51-200",
    "150-500人": "201-500",
    "500-2000人": "501-1000",
    "2000人以上": "5001+",
    "2000+": "5001+",
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
