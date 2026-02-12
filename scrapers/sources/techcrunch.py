"""TechCrunch scraper via Firecrawl.

T2 Open Web — scrapes TechCrunch AI category for startup funding news.
Strong Cloudflare protection requires Firecrawl. Extracts company names,
funding amounts, and round types from article listings and content.
"""

from __future__ import annotations

import logging
import re

from scrapers.base import BaseScraper, DiscoveredName, ScrapedProduct, SourceTier

logger = logging.getLogger(__name__)

_BASE_URL = "https://techcrunch.com"

# TechCrunch category/tag pages for AI content
_CATEGORY_URLS = [
    "/category/artificial-intelligence/",
    "/tag/ai-funding/",
    "/tag/generative-ai/",
    "/tag/machine-learning/",
]

# Regex patterns for extracting funding info from TC articles
_FUNDING_PATTERN = re.compile(
    r"(?:raises?|raised|secures?|secured|closes?|closed|lands?|landed|gets?|got)\s+"
    r"\$?([\d,.]+)\s*"
    r"(million|billion|M|B)\s*"
    r"(?:in\s+)?"
    r"(Series\s+[A-Z]\+?|Seed|Pre-Seed|Angel|growth|venture|"
    r"debt|convertible|extension|bridge)?\s*"
    r"(?:round|funding|financing)?",
    re.IGNORECASE,
)

# Extract company name from article titles
_TC_TITLE_COMPANY_PATTERN = re.compile(
    r"^([A-Z][A-Za-z0-9\s.&'-]{1,40}?)\s+"
    r"(?:raises?|secures?|closes?|lands?|gets?|launches?|announces?|unveils?|introduces?)",
    re.IGNORECASE,
)

# Article link pattern from listing pages
_ARTICLE_LINK_PATTERN = re.compile(
    r"\[([^\]]{10,150})\]\((https://techcrunch\.com/\d{4}/\d{2}/\d{2}/[^\s)]+)\)",
    re.MULTILINE,
)

# Alternative: heading-based article titles
_ARTICLE_HEADING_PATTERN = re.compile(
    r"#{1,3}\s+\[?([^\]\n#]{10,150})\]?" r"(?:\((https://techcrunch\.com/[^\s)]+)\))?",
    re.MULTILINE,
)

# Date extraction from article URLs
_DATE_PATTERN = re.compile(r"/(\d{4})/(\d{2})/(\d{2})/")


class TechCrunchScraper(BaseScraper):
    """Scrape TechCrunch for AI startup funding news.

    Uses Firecrawl to scrape AI category listing pages, then
    optionally scrapes individual articles for detailed funding data.
    """

    @property
    def source_name(self) -> str:
        return "techcrunch"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape TechCrunch AI category for funding news."""
        try:
            from scrapers.utils.firecrawl_client import FirecrawlClient
        except ImportError:
            logger.info("Firecrawl not available, skipping TechCrunch.")
            return []

        fc = FirecrawlClient()
        products: list[ScrapedProduct] = []
        seen_names: set[str] = set()

        try:
            for cat_url in _CATEGORY_URLS:
                if len(products) >= limit or fc.remaining_quota <= 0:
                    break

                url = f"{_BASE_URL}{cat_url}"
                logger.debug("TechCrunch: scraping %s", cat_url)

                result = fc.scrape_url(url, formats=["markdown"], wait_for=5000)
                if not result.success:
                    logger.debug("TechCrunch %s failed: %s", cat_url, result.error)
                    continue

                parsed = self._parse_listing(result.markdown, url, seen_names)
                products.extend(parsed)

        finally:
            fc.close()

        logger.info("TechCrunch: discovered %d companies", len(products))
        return products[:limit]

    def discover(self, limit: int = 100) -> list[DiscoveredName]:
        """Lightweight discovery from TechCrunch listings."""
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
        """Parse a TechCrunch listing page for funding articles."""
        if not markdown or len(markdown) < 200:
            return []

        products: list[ScrapedProduct] = []

        # Collect article entries
        articles: list[tuple[str, str]] = []

        for match in _ARTICLE_LINK_PATTERN.finditer(markdown):
            title = match.group(1).strip()
            article_url = match.group(2).strip()
            articles.append((title, article_url))

        if len(articles) < 3:
            for match in _ARTICLE_HEADING_PATTERN.finditer(markdown):
                title = match.group(1).strip()
                article_url = (match.group(2) or page_url).strip()
                if title and len(title) >= 10:
                    articles.append((title, article_url))

        for title, article_url in articles:
            # Try to extract company name from title
            company_match = _TC_TITLE_COMPANY_PATTERN.search(title)
            if not company_match:
                continue

            company_name = company_match.group(1).strip()
            if not company_name or len(company_name) < 2:
                continue

            key = company_name.lower()
            if key in seen:
                continue
            seen.add(key)

            # Try to extract funding info from title
            total_raised = None
            last_round = None
            funding_match = _FUNDING_PATTERN.search(title)

            if funding_match:
                amount_str = funding_match.group(1).replace(",", "")
                unit = funding_match.group(2).lower()
                round_type = funding_match.group(3)

                try:
                    amount = float(amount_str)
                    if unit in ("billion", "b"):
                        total_raised = amount * 1_000_000_000
                    else:
                        total_raised = amount * 1_000_000
                except ValueError:
                    pass

                if round_type:
                    last_round = round_type.strip().lower().replace(" ", "-")

            # Extract date from URL
            release_date = None
            date_match = _DATE_PATTERN.search(article_url)
            if date_match:
                release_date = (
                    f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                )

            extra: dict[str, str] = {"techcrunch_article_url": article_url}

            products.append(
                ScrapedProduct(
                    name=company_name,
                    source=self.source_name,
                    source_url=article_url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    description=title,
                    company_name=company_name,
                    company_total_raised_usd=total_raised,
                    company_last_round=last_round,
                    release_date=release_date,
                    status="active",
                    extra=extra,
                )
            )

        return products
