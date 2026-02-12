"""Toolify.ai scraper via Firecrawl.

T2 Open Web — AI tool ranking and traffic analytics platform.
Scrapes category pages for product discovery with traffic-based
popularity ranking data.
"""

from __future__ import annotations

import logging
import re

from scrapers.base import BaseScraper, DiscoveredName, ScrapedProduct, SourceTier

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.toolify.ai"

# Toolify category pages — organized by AI vertical
_CATEGORY_URLS = [
    "/category/ai-chatbot",
    "/category/ai-writing",
    "/category/ai-image",
    "/category/ai-video",
    "/category/ai-code",
    "/category/ai-audio",
    "/category/ai-design",
    "/category/ai-marketing",
    "/category/ai-search",
    "/category/ai-productivity",
    "/category/ai-education",
    "/category/ai-data-analysis",
    "/category/ai-developer-tools",
    "/category/ai-customer-service",
    "/category/ai-healthcare",
    "/category/ai-finance",
    "/category/ai-music",
    "/category/ai-3d",
    "/category/ai-translation",
]

# Map Toolify categories to our schema
_CATEGORY_MAP: dict[str, tuple[str, str, str | None]] = {
    # (product_type, category, sub_category)
    "ai-chatbot": ("app", "ai-app", "voice-assistant"),
    "ai-writing": ("app", "ai-app", "writing-copywriting"),
    "ai-image": ("app", "ai-app", "design-creative"),
    "ai-video": ("app", "ai-app", "video-editing"),
    "ai-code": ("dev-tool", "ai-dev-tool", "coding-assistant"),
    "ai-audio": ("app", "ai-app", "audio-speech"),
    "ai-design": ("app", "ai-app", "design-creative"),
    "ai-marketing": ("app", "ai-app", "marketing"),
    "ai-search": ("app", "ai-search", None),
    "ai-productivity": ("app", "ai-app", "workflow-automation"),
    "ai-education": ("app", "ai-app", "education-tutoring"),
    "ai-data-analysis": ("app", "ai-data", "data-analysis"),
    "ai-developer-tools": ("dev-tool", "ai-dev-tool", "ai-framework"),
    "ai-customer-service": ("app", "ai-app", "customer-service"),
    "ai-healthcare": ("app", "ai-science", "healthcare-medical"),
    "ai-finance": ("app", "ai-app", "finance-accounting"),
    "ai-music": ("app", "ai-app", "music-generation"),
    "ai-3d": ("app", "ai-app", "3d-generation"),
    "ai-translation": ("app", "ai-app", "translation"),
}

# Regex for extracting tool entries from Toolify markdown
# Toolify listings show: rank, tool name (linked), monthly visits, description
_TOOL_ENTRY_PATTERN = re.compile(
    r"(?:^|\n)"
    r"(?:\d+[\.\)]\s*)?"
    r"\[([^\]]{2,80})\]\((https?://[^\s)]+)\)"
    r"[^\n]*?"
    r"(?:(\d[\d,.]*[KMB]?)\s*(?:monthly\s*visits?|visits?/mo|visits?))?[^\n]*\n"
    r"([^\n]{10,500})?",
    re.MULTILINE | re.IGNORECASE,
)

# Alternative: simpler heading+description pattern
_TOOL_SIMPLE_PATTERN = re.compile(
    r"#{1,4}\s+\[?([^\]\n#]{2,80})\]?"
    r"(?:\((https?://[^\s)]+)\))?"
    r"\s*\n+"
    r"([^\n#]{10,500})",
    re.MULTILINE,
)

_SKIP_NAMES = frozenset(
    {
        "home",
        "about",
        "blog",
        "contact",
        "login",
        "sign up",
        "pricing",
        "privacy",
        "terms",
        "cookie",
        "faq",
        "all categories",
        "more tools",
        "load more",
        "next",
        "previous",
        "toolify",
        "submit",
        "categories",
    }
)


class ToolifyScraper(BaseScraper):
    """Scrape Toolify.ai for AI tool rankings and traffic data.

    Iterates category pages via Firecrawl to discover AI products
    with traffic-based ranking data.
    """

    @property
    def source_name(self) -> str:
        return "toolify"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape Toolify.ai category pages for AI tool rankings."""
        try:
            from scrapers.utils.firecrawl_client import FirecrawlClient
        except ImportError:
            logger.info("Firecrawl not available, skipping Toolify scraper.")
            return []

        fc = FirecrawlClient()
        products: list[ScrapedProduct] = []
        seen_names: set[str] = set()

        try:
            for cat_path in _CATEGORY_URLS:
                if len(products) >= limit:
                    break

                if fc.remaining_quota <= 0:
                    logger.warning(
                        "Firecrawl daily quota exhausted. Scraped %d products from Toolify.",
                        len(products),
                    )
                    break

                cat_slug = cat_path.rsplit("/", 1)[-1]
                url = f"{_BASE_URL}{cat_path}"

                logger.debug("Toolify: scraping category %s", cat_slug)
                result = fc.scrape_url(url, formats=["markdown"], wait_for=3000)

                if not result.success:
                    logger.debug("Toolify %s failed: %s", cat_slug, result.error)
                    continue

                parsed = self._parse_listing(result.markdown, cat_slug, url)

                for product in parsed:
                    name_lower = product.name.lower()
                    if name_lower in seen_names:
                        continue
                    seen_names.add(name_lower)
                    products.append(product)

                    if len(products) >= limit:
                        break

        finally:
            fc.close()

        logger.info("Toolify: discovered %d products", len(products))
        return products

    def discover(self, limit: int = 100) -> list[DiscoveredName]:
        """Lightweight discovery — names and URLs only."""
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
        self, markdown: str, cat_slug: str, page_url: str
    ) -> list[ScrapedProduct]:
        """Parse a Toolify category listing page."""
        if not markdown or len(markdown) < 100:
            return []

        products: list[ScrapedProduct] = []
        type_cat = _CATEGORY_MAP.get(cat_slug, ("app", "ai-app", None))
        product_type, category, sub_category = type_cat

        entries: list[tuple[str, str, str | None, str]] = []

        for match in _TOOL_ENTRY_PATTERN.finditer(markdown):
            name = match.group(1).strip()
            url = match.group(2).strip()
            visits = match.group(3)
            desc = (match.group(4) or "").strip()
            entries.append((name, url, visits, desc))

        if len(entries) < 3:
            for match in _TOOL_SIMPLE_PATTERN.finditer(markdown):
                name = match.group(1).strip()
                url = (match.group(2) or "").strip()
                desc = match.group(3).strip()
                if name and desc:
                    entries.append((name, url, None, desc))

        for name, url, monthly_visits, desc in entries:
            name_lower = name.lower().strip()

            if name_lower in _SKIP_NAMES:
                continue
            if len(name) < 2 or len(name) > 80:
                continue
            if name_lower.startswith(("http", "www.", "#", "/")):
                continue

            extra: dict[str, str] = {}
            if monthly_visits:
                extra["toolify_monthly_visits"] = monthly_visits

            products.append(
                ScrapedProduct(
                    name=name,
                    source=self.source_name,
                    source_url=page_url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    product_url=url if url else None,
                    description=_clean_description(desc) if desc else None,
                    product_type=product_type,
                    category=category,
                    sub_category=sub_category,
                    tags=(cat_slug.replace("-", " "),),
                    status="active",
                    extra=extra,
                )
            )

        return products


def _clean_description(text: str) -> str:
    """Clean up markdown artifacts from description."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_]{1,3}", "", text)
    text = text.strip()
    if len(text) > 500:
        text = text[:497] + "..."
    return text
