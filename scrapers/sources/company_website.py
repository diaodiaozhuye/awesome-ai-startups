"""Company/product website scraper for enrichment data.

T2 Open Web source — visits product and company websites to extract
descriptions, icons, pricing info, API docs links, and platform info.
Uses httpx for simple pages, falls back to Firecrawl for JS-heavy sites.
"""

from __future__ import annotations

import json
import logging
import re
import time

import httpx

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.config import DEFAULT_REQUEST_DELAY, PRODUCTS_DIR
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

# Patterns for extracting structured data from HTML
_OG_PATTERNS = {
    "og:title": re.compile(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    "og:description": re.compile(
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    "og:image": re.compile(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    "description": re.compile(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
}

_FAVICON_PATTERN = re.compile(
    r'<link[^>]+rel=["\'](?:icon|shortcut icon)["\'][^>]+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

_APPLE_TOUCH_PATTERN = re.compile(
    r'<link[^>]+rel=["\']apple-touch-icon["\'][^>]+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# Pricing page URL patterns
_PRICING_PATHS = ("/pricing", "/plans", "/price", "/plan")

# API docs URL patterns
_API_DOC_PATHS = ("/docs", "/api", "/developers", "/documentation", "/api-reference")


class CompanyWebsiteScraper(BaseScraper):
    """Scrape product/company websites for enrichment metadata.

    This is an enrichment scraper — it reads existing product JSON files,
    visits their product_url / company.website, and extracts:
    - description (og:description or meta description)
    - icon_url (favicon, apple-touch-icon)
    - pricing page detection
    - api_docs_url
    - platform indicators

    Uses httpx first, falls back to Firecrawl for JS-rendered sites.
    """

    @property
    def source_name(self) -> str:
        return "company_website"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Visit existing product URLs and extract metadata."""
        urls_to_visit = self._collect_urls(limit)
        if not urls_to_visit:
            return []

        client = create_http_client(timeout=15)
        products: list[ScrapedProduct] = []

        try:
            for product_name, url in urls_to_visit:
                result = self._scrape_website(client, product_name, url)
                if result:
                    products.append(result)
                time.sleep(DEFAULT_REQUEST_DELAY)

                if len(products) >= limit:
                    break
        finally:
            client.close()

        return products

    def _collect_urls(self, limit: int) -> list[tuple[str, str]]:
        """Collect URLs from existing product files that need enrichment."""
        urls: list[tuple[str, str]] = []

        if not PRODUCTS_DIR.exists():
            return urls

        for filepath in sorted(PRODUCTS_DIR.glob("*.json"))[: limit * 2]:
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            name = data.get("name", "")
            product_url = data.get("product_url", "")
            company_url = data.get("company", {}).get("website", "")

            # Only visit if we're missing key metadata
            needs_enrichment = (
                not data.get("icon_url")
                or not data.get("description")
                or data.get("meta", {}).get("data_quality_score", 1.0) < 0.5
            )

            # Ensure URLs have a scheme (some data has bare domains like "agpt.co")
            if product_url and not product_url.startswith("http"):
                product_url = f"https://{product_url}"
            if company_url and not company_url.startswith("http"):
                company_url = f"https://{company_url}"

            if needs_enrichment and product_url:
                urls.append((name, product_url))
            elif needs_enrichment and company_url:
                urls.append((name, company_url))

            if len(urls) >= limit:
                break

        return urls

    def _scrape_website(
        self,
        client: httpx.Client,
        product_name: str,
        url: str,
    ) -> ScrapedProduct | None:
        """Scrape a single website URL for metadata."""
        try:
            response = client.get(url)
            if not response.is_success:
                return self._try_firecrawl(product_name, url)

            html = response.text
            if len(html) < 100:
                return self._try_firecrawl(product_name, url)

            return self._extract_metadata(product_name, url, html)

        except (httpx.HTTPError, httpx.TimeoutException, OSError) as exc:
            logger.debug("Direct fetch failed for %s: %s, trying Firecrawl", url, exc)
            return self._try_firecrawl(product_name, url)

    def _extract_metadata(
        self, product_name: str, url: str, html: str
    ) -> ScrapedProduct | None:
        """Extract metadata from HTML content."""
        # OG / meta tags
        description = None
        icon_url = None
        og_image = None

        for key, pattern in _OG_PATTERNS.items():
            match = pattern.search(html)
            if match:
                value = match.group(1).strip()
                if key in ("og:description", "description") and not description:
                    description = value
                elif key == "og:image":
                    og_image = value

        # Favicon
        apple_match = _APPLE_TOUCH_PATTERN.search(html)
        favicon_match = _FAVICON_PATTERN.search(html)

        if apple_match:
            icon_url = _resolve_url(url, apple_match.group(1))
        elif favicon_match:
            icon_url = _resolve_url(url, favicon_match.group(1))

        if og_image:
            og_image = _resolve_url(url, og_image)

        # Detect pricing and API docs pages
        pricing_url = _detect_subpage(html, url, _PRICING_PATHS)
        api_docs_url = _detect_subpage(html, url, _API_DOC_PATHS)

        if not description and not icon_url:
            return None

        return ScrapedProduct(
            name=product_name,
            source="company_website",
            source_url=url,
            source_tier=SourceTier.T2_OPEN_WEB,
            product_url=url,
            description=description,
            icon_url=icon_url,
            company_logo_url=og_image,
            api_docs_url=api_docs_url,
            status="active",
            extra={
                k: v
                for k, v in {
                    "pricing_url": pricing_url,
                    "og_image": og_image,
                }.items()
                if v
            },
        )

    def _try_firecrawl(self, product_name: str, url: str) -> ScrapedProduct | None:
        """Attempt to fetch via Firecrawl as a fallback."""
        try:
            from scrapers.utils.firecrawl_client import FirecrawlClient

            fc = FirecrawlClient()
            try:
                if fc.remaining_quota <= 0:
                    return None

                result = fc.scrape_url(url, formats=["markdown", "html"])
                if not result.success:
                    return None

                # Extract from Firecrawl metadata
                meta = result.metadata
                description = meta.get("description") or meta.get("og:description")
                icon_url = meta.get("og:image")

                if not description and not result.markdown:
                    return None

                return ScrapedProduct(
                    name=product_name,
                    source="company_website",
                    source_url=url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    product_url=url,
                    description=description or result.markdown[:500],
                    icon_url=icon_url,
                    status="active",
                )
            finally:
                fc.close()
        except ImportError:
            logger.debug("Firecrawl not available, skipping %s", url)
            return None
        except (httpx.HTTPError, httpx.TimeoutException, ValueError, OSError):
            logger.debug("Firecrawl failed for %s", url, exc_info=True)
            return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_url(base_url: str, relative: str) -> str:
    """Resolve a potentially relative URL against a base URL."""
    if relative.startswith(("http://", "https://")):
        return relative
    if relative.startswith("//"):
        return "https:" + relative
    if relative.startswith("/"):
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{relative}"
    return base_url.rstrip("/") + "/" + relative


def _detect_subpage(
    html: str, base_url: str, path_patterns: tuple[str, ...]
) -> str | None:
    """Detect if the HTML contains links to specific subpages."""
    for path in path_patterns:
        # Look for href containing this path
        pattern = re.compile(
            rf'href=["\']([^"\']*{re.escape(path)}[^"\']*)["\']',
            re.IGNORECASE,
        )
        match = pattern.search(html)
        if match:
            return _resolve_url(base_url, match.group(1))
    return None
