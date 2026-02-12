"""AI工具集 (ai-bot.cn) scraper for Chinese AI product discovery.

T2 Open Web — Chinese AI tool directory with 1000+ tools. Uses httpx
to scrape the public category listing pages for Chinese-market AI tools.
No API key required.
"""

from __future__ import annotations

import logging
import re
import time

import httpx

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.config import DEFAULT_REQUEST_DELAY
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_BASE_URL = "https://ai-bot.cn"

# Category paths on ai-bot.cn (under /favorites/)
_CATEGORY_PATHS = [
    "ai-chatbots",
    "ai-writing-tools",
    "ai-image-tools",
    "ai-video-tools",
    "ai-audio-tools",
    "ai-coding-tools",
    "ai-design-tools",
    "ai-office-tools",
    "ai-search-engine",
    "ai-model-training",
]

# Map ai-bot.cn categories to our schema (product_type, category, sub_category)
_CATEGORY_MAP: dict[str, tuple[str, str, str | None]] = {
    "ai-chatbots": ("app", "ai-app", "voice-assistant"),
    "ai-writing-tools": ("app", "ai-app", "writing-copywriting"),
    "ai-image-tools": ("app", "ai-app", "design-creative"),
    "ai-video-tools": ("app", "ai-app", "video-editing"),
    "ai-audio-tools": ("app", "ai-app", "audio-speech"),
    "ai-coding-tools": ("dev-tool", "ai-dev-tool", "coding-assistant"),
    "ai-design-tools": ("app", "ai-app", "design-creative"),
    "ai-office-tools": ("app", "ai-app", "workflow-automation"),
    "ai-search-engine": ("app", "ai-search", None),
    "ai-model-training": ("framework", "ai-infrastructure", None),
}

# Regex: extract tool cards — ai-bot.cn uses <a href="URL" title="desc"><img><strong>Name</strong>
_TOOL_LINK_PATTERN = re.compile(
    r'<a[^>]*href=["\']([^"\']+)["\'][^>]*title=["\']([^"\']*)["\'][^>]*>'
    r".*?"
    r"<strong[^>]*>\s*([^<]{2,80})\s*</strong>",
    re.IGNORECASE | re.DOTALL,
)

# Fallback: simpler pattern for links with inner text
_SIMPLE_LINK_PATTERN = re.compile(
    r'<a[^>]*href=["\'](/sites/\d+\.html)["\'][^>]*>'
    r"\s*(?:<[^>]*>)*\s*([^<]{2,80})\s*(?:</[^>]*>)*\s*</a>",
    re.IGNORECASE | re.DOTALL,
)

# Icon extraction from <img> inside tool cards
_ICON_PATTERN = re.compile(
    r'<img[^>]*src=["\']([^"\']+)["\'][^>]*/?>',
    re.IGNORECASE,
)


class AiBotScraper(BaseScraper):
    """Scrape ai-bot.cn for Chinese AI product discovery.

    Uses direct HTTP requests since ai-bot.cn is a server-rendered
    site. Extracts tool names, URLs, descriptions, and icons from
    category listing pages.
    """

    @property
    def source_name(self) -> str:
        return "aibot"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape ai-bot.cn category pages for AI tool listings."""
        client = create_http_client()
        products: list[ScrapedProduct] = []
        seen_names: set[str] = set()

        try:
            for cat_slug in _CATEGORY_PATHS:
                if len(products) >= limit:
                    break

                url = f"{_BASE_URL}/favorites/{cat_slug}/"
                logger.debug("aibot: scraping %s", cat_slug)

                try:
                    response = client.get(url)
                    response.raise_for_status()
                except (httpx.HTTPError, httpx.TimeoutException, OSError) as exc:
                    logger.debug("aibot %s failed: %s", cat_slug, exc)
                    time.sleep(DEFAULT_REQUEST_DELAY)
                    continue

                html = response.text
                parsed = self._parse_listing(html, cat_slug, url)

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

        logger.info("aibot: discovered %d products", len(products))
        return products

    def _parse_listing(
        self, html: str, cat_slug: str, page_url: str
    ) -> list[ScrapedProduct]:
        """Parse an ai-bot.cn category listing page."""
        if not html or len(html) < 200:
            return []

        type_cat = _CATEGORY_MAP.get(cat_slug, ("app", "ai-app", None))
        product_type, category, sub_category = type_cat

        entries = self._extract_tools(html)
        products: list[ScrapedProduct] = []

        for name, tool_url, description, icon_url in entries:
            name = name.strip()
            if not name or len(name) < 2 or len(name) > 80:
                continue

            # Resolve relative URLs
            if tool_url and not tool_url.startswith("http"):
                tool_url = (
                    f"{_BASE_URL}{tool_url}"
                    if tool_url.startswith("/")
                    else f"{_BASE_URL}/{tool_url}"
                )
            if icon_url and not icon_url.startswith("http"):
                icon_url = (
                    f"{_BASE_URL}{icon_url}" if icon_url.startswith("/") else None
                )

            name_zh = name if _has_chinese(name) else None
            desc_zh = description if description and _has_chinese(description) else None

            products.append(
                ScrapedProduct(
                    name=name,
                    source=self.source_name,
                    source_url=page_url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    name_zh=name_zh,
                    product_url=tool_url or None,
                    description=description or None,
                    description_zh=desc_zh,
                    icon_url=icon_url or None,
                    product_type=product_type,
                    category=category,
                    sub_category=sub_category,
                    tags=(cat_slug,),
                    status="active",
                )
            )

        return products

    def _extract_tools(self, html: str) -> list[tuple[str, str, str, str]]:
        """Extract (name, url, description, icon_url) tuples from HTML."""
        entries: list[tuple[str, str, str, str]] = []
        seen_urls: set[str] = set()

        # Strategy 1: structured tool cards with title attribute
        for match in _TOOL_LINK_PATTERN.finditer(html):
            url = match.group(1).strip()
            description = match.group(2).strip()
            name = _strip_html(match.group(3)).strip()

            if not name or url in seen_urls:
                continue
            seen_urls.add(url)

            # Try to find icon nearby
            icon = ""
            card_html = match.group(0)
            icon_match = _ICON_PATTERN.search(card_html)
            if icon_match:
                icon = icon_match.group(1).strip()

            entries.append((name, url, description, icon))

        if entries:
            return entries

        # Strategy 2: fallback — simpler link pattern
        for match in _SIMPLE_LINK_PATTERN.finditer(html):
            url = match.group(1).strip()
            name = _strip_html(match.group(2)).strip()

            if not name or url in seen_urls:
                continue
            seen_urls.add(url)
            entries.append((name, url, "", ""))

        return entries


def _has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text).strip()
