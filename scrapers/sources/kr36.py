"""36Kr scraper via Firecrawl.

T2 Open Web — Chinese tech media and startup news platform.
Scrapes AI-related articles for Chinese AI company funding news,
product launches, and company information.
"""

from __future__ import annotations

import logging
import re

from scrapers.base import BaseScraper, DiscoveredName, ScrapedProduct, SourceTier

logger = logging.getLogger(__name__)

_BASE_URL = "https://36kr.com"

# Category/tag pages for AI content
_SCRAPE_URLS = [
    "/information/AI/",
    "/information/web3/",
    "/newsflashes/cate/71",  # AI category flash news
]

# Search URLs for AI-related content
_SEARCH_QUERIES = [
    "人工智能 融资",
    "大模型 融资",
    "AI 创业",
    "AIGC 融资",
    "智能体 AI",
    "自动驾驶 融资",
    "AI 芯片",
    "机器人 融资",
]

# Regex patterns for extracting funding info from article markdown
_FUNDING_PATTERN = re.compile(
    r"(?:获得|完成|宣布|获|融资)"
    r"[^，。、\n]{0,20}?"
    r"(\d+(?:\.\d+)?)\s*"
    r"(亿|万|百万|千万|亿美元|万美元|百万美元|千万美元|亿元|万元)"
    r"[^，。、\n]{0,30}?"
    r"(天使轮|种子轮|Pre-A轮|A轮|A\+轮|B轮|B\+轮|C轮|D轮|E轮|"
    r"Pre-IPO|IPO|战略融资|Series [A-Z]|Seed|Angel)?",
    re.IGNORECASE,
)

# Extract company name from funding news
_COMPANY_NAME_PATTERN = re.compile(
    r'(?:^|\n|【)'
    r'(?:[「"\x22])?([^\s「」\u201c\u201d\x22]{2,20})(?:[」"\x22])?[，,]?\s*'
    r'(?:获得|完成|宣布|拿到|近日)',
    re.MULTILINE,
)

# Article card pattern from listing pages
_ARTICLE_CARD_PATTERN = re.compile(
    r'\[([^\]]{5,100})\]\(((?:/p/|https://36kr\.com/p/)\d+)\)',
    re.MULTILINE,
)

# Company name pattern from article titles
_TITLE_COMPANY_PATTERN = re.compile(
    r'(?:[「"\x22])?([^\s「」\u201c\u201d\x22，,]{2,15})(?:[」"\x22])?[，,]?\s*'
    r'(?:获|完成|宣布|拿到|发布|推出|上线|开源)',
)


class Kr36Scraper(BaseScraper):
    """Scrape 36Kr for Chinese AI company funding news.

    Uses Firecrawl to scrape AI category pages and search results,
    extracting company names, funding amounts, and product announcements
    from Chinese tech media articles.
    """

    @property
    def source_name(self) -> str:
        return "36kr"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape 36Kr for AI funding news and product announcements."""
        try:
            from scrapers.utils.firecrawl_client import FirecrawlClient
        except ImportError:
            logger.info("Firecrawl not available, skipping 36Kr scraper.")
            return []

        fc = FirecrawlClient()
        products: list[ScrapedProduct] = []
        seen_names: set[str] = set()

        try:
            # Phase 1: Scrape category listing pages
            for cat_url in _SCRAPE_URLS:
                if len(products) >= limit or fc.remaining_quota <= 0:
                    break

                url = f"{_BASE_URL}{cat_url}"
                logger.debug("36kr: scraping %s", cat_url)

                result = fc.scrape_url(url, formats=["markdown"], wait_for=3000)
                if not result.success:
                    logger.debug("36kr %s failed: %s", cat_url, result.error)
                    continue

                parsed = self._parse_listing(result.markdown, url, seen_names)
                products.extend(parsed)

            # Phase 2: Scrape individual articles for detailed funding info
            article_urls = self._extract_article_urls(products)
            for article_url in article_urls[:10]:  # Limit article scrapes
                if len(products) >= limit or fc.remaining_quota <= 0:
                    break

                full_url = article_url
                if not full_url.startswith("http"):
                    full_url = f"{_BASE_URL}{article_url}"

                result = fc.scrape_url(full_url, formats=["markdown"])
                if not result.success:
                    continue

                enriched = self._parse_article(result.markdown, full_url, seen_names)
                products.extend(enriched)

        finally:
            fc.close()

        logger.info("36kr: discovered %d companies/products", len(products))
        return products[:limit]

    def discover(self, limit: int = 100) -> list[DiscoveredName]:
        """Lightweight discovery from 36Kr listings."""
        products = self.scrape(limit=limit)
        return [
            DiscoveredName(
                name=p.name,
                source=self.source_name,
                source_url=p.source_url,
            )
            for p in products
        ]

    def _parse_listing(
        self, markdown: str, page_url: str, seen: set[str]
    ) -> list[ScrapedProduct]:
        """Parse a 36Kr listing page for article titles with company names."""
        if not markdown or len(markdown) < 100:
            return []

        products: list[ScrapedProduct] = []

        for match in _ARTICLE_CARD_PATTERN.finditer(markdown):
            title = match.group(1).strip()
            article_path = match.group(2).strip()

            # Try to extract company name from title
            company_match = _TITLE_COMPANY_PATTERN.search(title)
            if not company_match:
                continue

            company_name = company_match.group(1).strip()
            if not company_name or len(company_name) < 2:
                continue

            key = company_name.lower()
            if key in seen:
                continue
            seen.add(key)

            # Determine if this is a funding article
            funding_info = _extract_funding_from_title(title)

            article_url = article_path
            if not article_url.startswith("http"):
                article_url = f"{_BASE_URL}{article_path}"

            extra: dict[str, str] = {"36kr_article_url": article_url}
            if funding_info:
                extra["36kr_funding_info"] = funding_info

            products.append(
                ScrapedProduct(
                    name=company_name,
                    source=self.source_name,
                    source_url=article_url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    name_zh=company_name if _has_chinese(company_name) else None,
                    description=title,
                    description_zh=title if _has_chinese(title) else None,
                    company_name=company_name,
                    company_name_zh=company_name if _has_chinese(company_name) else None,
                    status="active",
                    extra=extra,
                )
            )

        return products

    def _parse_article(
        self, markdown: str, article_url: str, seen: set[str]
    ) -> list[ScrapedProduct]:
        """Parse a full 36Kr article for detailed funding information."""
        if not markdown or len(markdown) < 200:
            return []

        products: list[ScrapedProduct] = []

        # Extract company names mentioned in funding context
        for match in _COMPANY_NAME_PATTERN.finditer(markdown):
            company_name = match.group(1).strip()

            key = company_name.lower()
            if key in seen or len(company_name) < 2 or len(company_name) > 20:
                continue
            seen.add(key)

            # Try to extract funding details
            funding_match = _FUNDING_PATTERN.search(
                markdown[match.start():match.start() + 200]
            )

            total_raised = None
            last_round = None
            extra: dict[str, str] = {"36kr_article_url": article_url}

            if funding_match:
                amount = float(funding_match.group(1))
                unit = funding_match.group(2)
                round_type = funding_match.group(3)

                total_raised = _convert_chinese_amount(amount, unit)
                if round_type:
                    last_round = _normalize_round(round_type)
                    extra["funding_round"] = round_type

            products.append(
                ScrapedProduct(
                    name=company_name,
                    source=self.source_name,
                    source_url=article_url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    name_zh=company_name if _has_chinese(company_name) else None,
                    company_name=company_name,
                    company_name_zh=company_name if _has_chinese(company_name) else None,
                    company_total_raised_usd=total_raised,
                    company_last_round=last_round,
                    status="active",
                    extra=extra,
                )
            )

        return products

    def _extract_article_urls(self, products: list[ScrapedProduct]) -> list[str]:
        """Extract unique article URLs from scraped products."""
        urls: list[str] = []
        seen: set[str] = set()
        for p in products:
            url = p.extra.get("36kr_article_url", "")
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
        return urls


def _has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _extract_funding_from_title(title: str) -> str | None:
    """Extract a short funding summary from article title."""
    match = _FUNDING_PATTERN.search(title)
    if match:
        amount = match.group(1)
        unit = match.group(2)
        round_type = match.group(3) or ""
        return f"{amount}{unit} {round_type}".strip()
    return None


def _convert_chinese_amount(amount: float, unit: str) -> float | None:
    """Convert Chinese monetary amounts to USD.

    Uses approximate CNY/USD rate of 7.2 for RMB amounts.
    """
    cny_to_usd = 1.0 / 7.2

    if "美元" in unit:
        # Already in USD
        if "亿" in unit:
            return amount * 100_000_000
        if "千万" in unit:
            return amount * 10_000_000
        if "百万" in unit:
            return amount * 1_000_000
        if "万" in unit:
            return amount * 10_000
        return amount
    else:
        # Assume RMB
        if "亿" in unit:
            return amount * 100_000_000 * cny_to_usd
        if "千万" in unit:
            return amount * 10_000_000 * cny_to_usd
        if "百万" in unit:
            return amount * 1_000_000 * cny_to_usd
        if "万" in unit:
            return amount * 10_000 * cny_to_usd
        return amount * cny_to_usd


def _normalize_round(raw: str) -> str:
    """Normalize funding round name to slug format."""
    mapping: dict[str, str] = {
        "天使轮": "angel",
        "种子轮": "seed",
        "Pre-A轮": "pre-a",
        "A轮": "series-a",
        "A+轮": "series-a-plus",
        "B轮": "series-b",
        "B+轮": "series-b-plus",
        "C轮": "series-c",
        "D轮": "series-d",
        "E轮": "series-e",
        "Pre-IPO": "pre-ipo",
        "IPO": "ipo",
        "战略融资": "strategic",
    }
    return mapping.get(raw, raw.lower().replace(" ", "-"))
