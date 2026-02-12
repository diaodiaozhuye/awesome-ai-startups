"""AI集 (aiji.com) scraper for Chinese AI product discovery.

T2 Open Web — Chinese AI product directory. Uses httpx to scrape
the public directory pages for Chinese-market AI tools and products.
"""

from __future__ import annotations

import logging
import re
import time

import httpx

from scrapers.base import BaseScraper, DiscoveredName, ScrapedProduct, SourceTier
from scrapers.config import DEFAULT_REQUEST_DELAY
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.aiji.com"

# Category paths on aiji.com
_CATEGORY_PATHS = [
    "/ai-tools",
    "/ai-chat",
    "/ai-writing",
    "/ai-image",
    "/ai-video",
    "/ai-audio",
    "/ai-code",
    "/ai-design",
    "/ai-marketing",
    "/ai-education",
    "/ai-office",
    "/ai-translation",
    "/ai-search",
]

# Map aiji.com categories to our schema
_CATEGORY_MAP: dict[str, tuple[str, str, str | None]] = {
    "ai-tools": ("app", "ai-app", None),
    "ai-chat": ("app", "ai-app", "voice-assistant"),
    "ai-writing": ("app", "ai-app", "writing-copywriting"),
    "ai-image": ("app", "ai-app", "design-creative"),
    "ai-video": ("app", "ai-app", "video-editing"),
    "ai-audio": ("app", "ai-app", "audio-speech"),
    "ai-code": ("dev-tool", "ai-dev-tool", "coding-assistant"),
    "ai-design": ("app", "ai-app", "design-creative"),
    "ai-marketing": ("app", "ai-app", "marketing"),
    "ai-education": ("app", "ai-app", "education-tutoring"),
    "ai-office": ("app", "ai-app", "workflow-automation"),
    "ai-translation": ("app", "ai-app", "translation"),
    "ai-search": ("app", "ai-search", None),
}

# Regex patterns for extracting tool info from HTML
_TOOL_CARD_PATTERN = re.compile(
    r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>'
    r"[^<]*?"
    r'<(?:h[2-4]|div|span)[^>]*class=["\'][^"\']*(?:title|name)[^"\']*["\'][^>]*>'
    r"\s*([^<]{2,80})\s*"
    r"</(?:h[2-4]|div|span)>",
    re.IGNORECASE,
)

_DESCRIPTION_PATTERN = re.compile(
    r'<(?:p|div|span)[^>]*class=["\'][^"\']*(?:desc|description|intro|summary)[^"\']*["\'][^>]*>'
    r"\s*([^<]{10,500})\s*"
    r"</(?:p|div|span)>",
    re.IGNORECASE,
)


class AijiScraper(BaseScraper):
    """Scrape aiji.com for Chinese AI product discovery.

    Uses direct HTTP requests since aiji.com is a simple server-rendered
    site without heavy anti-bot protection. Extracts tool names, URLs,
    and Chinese descriptions from category listing pages.
    """

    @property
    def source_name(self) -> str:
        return "aiji"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape aiji.com category pages for AI tool listings."""
        client = create_http_client()
        products: list[ScrapedProduct] = []
        seen_names: set[str] = set()

        try:
            for cat_path in _CATEGORY_PATHS:
                if len(products) >= limit:
                    break

                url = f"{_BASE_URL}{cat_path}"
                cat_slug = cat_path.strip("/")

                logger.debug("aiji: scraping %s", cat_slug)

                try:
                    response = client.get(url)
                    response.raise_for_status()
                except (httpx.HTTPError, httpx.TimeoutException) as e:
                    logger.debug("aiji %s failed: %s", cat_slug, e)
                    time.sleep(DEFAULT_REQUEST_DELAY)
                    continue

                html = response.text
                parsed = self._parse_listing_html(html, cat_slug, url)

                for product in parsed:
                    name_lower = product.name.lower()
                    if name_lower in seen_names:
                        continue
                    seen_names.add(name_lower)
                    products.append(product)

                    if len(products) >= limit:
                        break

                time.sleep(DEFAULT_REQUEST_DELAY)

        finally:
            client.close()

        logger.info("aiji: discovered %d products", len(products))
        return products

    def discover(self, limit: int = 100) -> list[DiscoveredName]:
        """Lightweight discovery for aiji.com."""
        products = self.scrape(limit=limit)
        return [
            DiscoveredName(
                name=p.name,
                source=self.source_name,
                source_url=p.source_url,
            )
            for p in products
        ]

    def _parse_listing_html(
        self, html: str, cat_slug: str, page_url: str
    ) -> list[ScrapedProduct]:
        """Parse an aiji.com category listing page HTML."""
        if not html or len(html) < 200:
            return []

        products: list[ScrapedProduct] = []
        type_cat = _CATEGORY_MAP.get(cat_slug, ("app", "ai-app", None))
        product_type, category, sub_category = type_cat

        # Try to extract tool cards from HTML
        tool_entries = self._extract_tool_cards(html)

        for name, tool_url, description in tool_entries:
            name = name.strip()
            if not name or len(name) < 2 or len(name) > 80:
                continue

            # Resolve relative URLs
            if tool_url and not tool_url.startswith("http"):
                if tool_url.startswith("/"):
                    tool_url = f"{_BASE_URL}{tool_url}"
                else:
                    tool_url = f"{_BASE_URL}/{tool_url}"

            # Determine if name is Chinese
            name_zh = name if _has_chinese(name) else None
            name_en = name if not _has_chinese(name) else None

            products.append(
                ScrapedProduct(
                    name=name_en or name,
                    source=self.source_name,
                    source_url=page_url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    name_zh=name_zh,
                    product_url=tool_url if tool_url else None,
                    description=description if description else None,
                    description_zh=(
                        description
                        if description and _has_chinese(description)
                        else None
                    ),
                    product_type=product_type,
                    category=category,
                    sub_category=sub_category,
                    tags=(cat_slug.replace("-", " "),),
                    status="active",
                )
            )

        return products

    def _extract_tool_cards(self, html: str) -> list[tuple[str, str, str]]:
        """Extract tool name, URL, and description from HTML.

        Uses multiple strategies: card patterns, link+title combos,
        and falls back to meta/structured data.
        """
        entries: list[tuple[str, str, str]] = []

        # Strategy 1: look for structured tool cards
        for match in _TOOL_CARD_PATTERN.finditer(html):
            url = match.group(1).strip()
            name = _strip_html(match.group(2)).strip()
            if name and url:
                # Try to find description near this card
                desc = self._find_nearby_description(html, match.end())
                entries.append((name, url, desc))

        if entries:
            return entries

        # Strategy 2: find all internal links with reasonable names
        link_pattern = re.compile(
            r'<a[^>]*href=["\'](/(?:tool|detail|app|product)/[^"\']+)["\'][^>]*>'
            r"\s*([^<]{2,80})\s*</a>",
            re.IGNORECASE,
        )
        for match in link_pattern.finditer(html):
            url = match.group(1).strip()
            name = _strip_html(match.group(2)).strip()
            if name and len(name) >= 2:
                entries.append((name, url, ""))

        return entries

    def _find_nearby_description(self, html: str, pos: int) -> str:
        """Look for a description element near the given position."""
        # Search in a 1000-char window after the tool name
        window = html[pos : pos + 1000]
        match = _DESCRIPTION_PATTERN.search(window)
        if match:
            return _strip_html(match.group(1)).strip()
        return ""


def _has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text).strip()
