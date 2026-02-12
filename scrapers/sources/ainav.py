"""AI导航网 (ainav.cn) scraper for Chinese AI product discovery.

T2 Open Web — Chinese AI tool directory with 1000+ tools. Uses httpx
to scrape the public category listing pages. Category URLs use
URL-encoded Chinese path segments.
No API key required.
"""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import quote

import httpx

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.config import DEFAULT_REQUEST_DELAY
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.ainav.cn"

# Category paths use Chinese names (will be URL-encoded for requests)
# Format: (display_name, url_path_segment, product_type, category, sub_category)
_CATEGORIES: list[tuple[str, str, str, str, str | None]] = [
    ("AI对话聊天", "ai对话聊天", "app", "ai-app", "voice-assistant"),
    ("AI文本写作", "ai文本写作", "app", "ai-app", "writing-copywriting"),
    ("AI绘画生成", "ai绘画生成", "app", "ai-app", "design-creative"),
    ("AI视频工具", "ai视频工具", "app", "ai-app", "video-editing"),
    ("AI音频工具", "ai音频工具", "app", "ai-app", "audio-speech"),
    ("AI图片处理", "ai图片处理", "app", "ai-app", "design-creative"),
    ("AI编程工具", "ai编程工具", "dev-tool", "ai-dev-tool", "coding-assistant"),
    ("AI办公工具", "ai办公工具", "app", "ai-app", "workflow-automation"),
    ("AI搜索引擎", "ai搜索引擎", "app", "ai-search", None),
    ("AI训练模型", "ai训练模型", "framework", "ai-infrastructure", None),
]

# Regex: tool cards — ainav.cn uses <a href="/sites/ID.html" data-url="PRODUCT_URL" title="DESC">
# with <strong>Name</strong> inside the card body.
_TOOL_CARD_PATTERN = re.compile(
    r'<a[^>]*href=["\']([^"\']*?/sites/\d+\.html)["\']'
    r'[^>]*data-url=["\']([^"\']*)["\']'
    r'[^>]*title=["\']([^"\']*)["\'][^>]*>'
    r".*?"
    r"<strong[^>]*>\s*([^<]{2,80})\s*</strong>",
    re.IGNORECASE | re.DOTALL,
)

# Icon pattern
_ICON_PATTERN = re.compile(
    r'<img[^>]*src=["\']([^"\']+)["\'][^>]*/?>',
    re.IGNORECASE,
)


class AiNavScraper(BaseScraper):
    """Scrape ainav.cn for Chinese AI product discovery.

    Uses direct HTTP requests. Category pages use URL-encoded Chinese
    path segments (e.g., /favorites/ai对话聊天).
    """

    @property
    def source_name(self) -> str:
        return "ainav"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape ainav.cn category pages for AI tool listings."""
        client = create_http_client()
        products: list[ScrapedProduct] = []
        seen_names: set[str] = set()

        try:
            for display_name, path_seg, product_type, category, sub_cat in _CATEGORIES:
                if len(products) >= limit:
                    break

                encoded_path = quote(path_seg, safe="")
                url = f"{_BASE_URL}/favorites/{encoded_path}"
                logger.debug("ainav: scraping %s", display_name)

                try:
                    response = client.get(url)
                    response.raise_for_status()
                except (httpx.HTTPError, httpx.TimeoutException, OSError) as exc:
                    logger.debug("ainav %s failed: %s", display_name, exc)
                    time.sleep(DEFAULT_REQUEST_DELAY)
                    continue

                html = response.text
                parsed = self._parse_listing(
                    html, url, product_type, category, sub_cat, path_seg
                )

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

        logger.info("ainav: discovered %d products", len(products))
        return products

    def _parse_listing(
        self,
        html: str,
        page_url: str,
        product_type: str,
        category: str,
        sub_category: str | None,
        tag: str,
    ) -> list[ScrapedProduct]:
        """Parse an ainav.cn category listing page."""
        if not html or len(html) < 200:
            return []

        entries = self._extract_tools(html)
        products: list[ScrapedProduct] = []

        for name, detail_url, description, icon_url, product_url in entries:
            name = name.strip()
            if not name or len(name) < 2 or len(name) > 80:
                continue

            # Resolve relative URLs
            if detail_url and not detail_url.startswith("http"):
                detail_url = f"{_BASE_URL}{detail_url}"

            # Use direct product URL if available, else detail page
            final_url = product_url or detail_url or None

            if icon_url and not icon_url.startswith("http"):
                icon_url = (
                    f"{_BASE_URL}{icon_url}" if icon_url.startswith("/") else None
                )

            name_zh = name if _has_chinese(name) else None
            desc_zh = (
                description if description and _has_chinese(description) else None
            )

            products.append(
                ScrapedProduct(
                    name=name,
                    source=self.source_name,
                    source_url=page_url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    name_zh=name_zh,
                    product_url=final_url,
                    description=description or None,
                    description_zh=desc_zh,
                    icon_url=icon_url or None,
                    product_type=product_type,
                    category=category,
                    sub_category=sub_category,
                    tags=(tag,),
                    status="active",
                )
            )

        return products

    def _extract_tools(
        self, html: str
    ) -> list[tuple[str, str, str, str, str]]:
        """Extract (name, detail_url, description, icon_url, product_url) from HTML.

        The regex captures 4 groups from ainav.cn card structure:
        1. detail_url (/sites/ID.html)
        2. product_url (data-url attribute — the real product website)
        3. description (title attribute)
        4. name (<strong> text)
        """
        entries: list[tuple[str, str, str, str, str]] = []
        seen_urls: set[str] = set()

        for match in _TOOL_CARD_PATTERN.finditer(html):
            detail_url = match.group(1).strip()
            product_url = match.group(2).strip()
            description = match.group(3).strip()
            name = _strip_html(match.group(4)).strip()

            if not name or detail_url in seen_urls:
                continue
            seen_urls.add(detail_url)

            # Extract icon from card HTML
            icon = ""
            card_html = match.group(0)
            icon_match = _ICON_PATTERN.search(card_html)
            if icon_match:
                icon = icon_match.group(1).strip()
                # Skip generic placeholder favicons
                if "favicon.png" in icon or "default" in icon:
                    icon = ""

            entries.append((name, detail_url, description, icon, product_url))

        return entries


def _has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text).strip()
