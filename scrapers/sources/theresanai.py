"""There's An AI For That (TAAFT) scraper via Firecrawl.

T2 Open Web — one of the largest AI product directories with 14,000+
tools. Scrapes category listing pages to discover new AI products in bulk.
Uses Firecrawl because the site has bot protection.
"""

from __future__ import annotations

import logging
import re

from scrapers.base import BaseScraper, DiscoveredName, ScrapedProduct, SourceTier

logger = logging.getLogger(__name__)

# Base URL for TAAFT
_BASE_URL = "https://theresanaiforthat.com"

# Category pages to scrape — covers the major AI tool verticals
_CATEGORY_URLS = [
    "/s/text-generators",
    "/s/image-generators",
    "/s/video-generators",
    "/s/code-assistants",
    "/s/chatbots",
    "/s/writing-assistants",
    "/s/marketing",
    "/s/productivity",
    "/s/music-generators",
    "/s/search-engines",
    "/s/data-analysis",
    "/s/education",
    "/s/design",
    "/s/developer-tools",
    "/s/customer-support",
    "/s/healthcare",
    "/s/finance",
    "/s/legal",
    "/s/speech",
    "/s/audio",
    "/s/3d",
    "/s/robotics",
    "/s/autonomous-vehicles",
    "/s/cybersecurity",
    "/s/gaming",
]

# Map TAAFT categories to our product_type/category schema
_CATEGORY_MAP: dict[str, tuple[str, str]] = {
    "text-generators": ("llm", "ai-model"),
    "image-generators": ("app", "ai-app"),
    "video-generators": ("app", "ai-app"),
    "code-assistants": ("dev-tool", "ai-dev-tool"),
    "chatbots": ("app", "ai-app"),
    "writing-assistants": ("app", "ai-app"),
    "marketing": ("app", "ai-app"),
    "productivity": ("app", "ai-app"),
    "music-generators": ("app", "ai-app"),
    "search-engines": ("app", "ai-search"),
    "data-analysis": ("app", "ai-data"),
    "education": ("app", "ai-app"),
    "design": ("app", "ai-app"),
    "developer-tools": ("dev-tool", "ai-dev-tool"),
    "customer-support": ("app", "ai-app"),
    "healthcare": ("app", "ai-science"),
    "finance": ("app", "ai-app"),
    "legal": ("app", "ai-app"),
    "speech": ("app", "ai-app"),
    "audio": ("app", "ai-app"),
    "3d": ("app", "ai-app"),
    "robotics": ("hardware", "ai-hardware"),
    "autonomous-vehicles": ("hardware", "ai-hardware"),
    "cybersecurity": ("app", "ai-security"),
    "gaming": ("app", "ai-app"),
}

# Regex patterns for extracting tool info from markdown
# TAAFT markdown typically has tool cards with name, description, URL
_TOOL_BLOCK_PATTERN = re.compile(
    r"\[([^\]]{2,80})\]\((https?://[^\s)]+)\)" r"[^\n]*\n+" r"([^\n]{10,500})",
    re.MULTILINE,
)

# Alternative pattern: tool name as heading with description below
_TOOL_HEADING_PATTERN = re.compile(
    r"#{1,4}\s+\[?([^\]\n#]{2,80})\]?"
    r"(?:\((https?://[^\s)]+)\))?"
    r"\s*\n+"
    r"([^\n#]{10,500})",
    re.MULTILINE,
)

# Filter out navigation links, social media, etc.
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
        "help",
        "twitter",
        "linkedin",
        "facebook",
        "github",
        "discord",
        "newsletter",
        "submit",
        "categories",
        "all tools",
        "more",
        "load more",
        "next",
        "previous",
        "back",
    }
)


class TAAScraper(BaseScraper):
    """Scrape There's An AI For That for AI tool discovery.

    Iterates over category listing pages via Firecrawl, extracting
    tool names, descriptions, and URLs. Designed for bulk product
    discovery — the site indexes 14,000+ AI tools.
    """

    @property
    def source_name(self) -> str:
        return "theresanaiforthat"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape TAAFT category pages for AI tool listings."""
        try:
            from scrapers.utils.firecrawl_client import FirecrawlClient
        except ImportError:
            logger.info("Firecrawl not available, skipping TAAFT scraper.")
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
                        "Firecrawl daily quota exhausted. Scraped %d products from TAAFT.",
                        len(products),
                    )
                    break

                cat_slug = cat_path.rsplit("/", 1)[-1]
                url = f"{_BASE_URL}{cat_path}"

                logger.debug("TAAFT: scraping category %s", cat_slug)
                result = fc.scrape_url(url, formats=["markdown"], wait_for=3000)

                if not result.success:
                    logger.debug("TAAFT %s failed: %s", cat_slug, result.error)
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

        logger.info("TAAFT: discovered %d products", len(products))
        return products

    def discover(self, limit: int = 100) -> list[DiscoveredName]:
        """Lightweight discovery — extract just names and URLs."""
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
        """Parse TAAFT category listing markdown into products."""
        if not markdown or len(markdown) < 100:
            return []

        products: list[ScrapedProduct] = []
        product_type, category = _CATEGORY_MAP.get(cat_slug, ("app", "ai-app"))

        # Try both patterns
        entries: list[tuple[str, str, str]] = []

        for match in _TOOL_BLOCK_PATTERN.finditer(markdown):
            name = match.group(1).strip()
            url = match.group(2).strip()
            desc = match.group(3).strip()
            entries.append((name, url, desc))

        if len(entries) < 3:
            for match in _TOOL_HEADING_PATTERN.finditer(markdown):
                name = match.group(1).strip()
                url = (match.group(2) or "").strip()
                desc = match.group(3).strip()
                if name and desc:
                    entries.append((name, url, desc))

        for name, url, desc in entries:
            name_lower = name.lower().strip()

            if name_lower in _SKIP_NAMES:
                continue
            if len(name) < 2 or len(name) > 80:
                continue
            if len(desc) < 10:
                continue
            # Skip if name looks like a navigation element
            if name_lower.startswith(("http", "www.", "#", "/")):
                continue

            sub_category = _taaft_to_subcategory(cat_slug)

            products.append(
                ScrapedProduct(
                    name=name,
                    source=self.source_name,
                    source_url=page_url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    product_url=url if url else None,
                    description=_clean_description(desc),
                    product_type=product_type,
                    category=category,
                    sub_category=sub_category,
                    tags=(cat_slug.replace("-", " "),),
                    status="active",
                )
            )

        return products


def _taaft_to_subcategory(cat_slug: str) -> str | None:
    """Map TAAFT category slug to our sub_category values."""
    mapping: dict[str, str] = {
        "text-generators": "text-generation",
        "image-generators": "image-generation",
        "video-generators": "video-generation",
        "code-assistants": "coding-assistant",
        "chatbots": "voice-assistant",
        "writing-assistants": "writing-copywriting",
        "marketing": "marketing",
        "music-generators": "music-generation",
        "search-engines": "ai-search",
        "data-analysis": "data-analysis",
        "education": "education-tutoring",
        "design": "design-creative",
        "developer-tools": "ai-framework",
        "customer-support": "customer-service",
        "healthcare": "healthcare-medical",
        "finance": "finance-accounting",
        "legal": "legal",
        "speech": "audio-speech",
        "audio": "audio-speech",
        "3d": "3d-generation",
        "robotics": "robot",
        "autonomous-vehicles": "autonomous-vehicle",
        "cybersecurity": "ai-security",
    }
    return mapping.get(cat_slug)


def _clean_description(text: str) -> str:
    """Clean up a TAAFT description string."""
    # Remove markdown artifacts
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_]{1,3}", "", text)
    text = text.strip()
    # Truncate if excessively long
    if len(text) > 500:
        text = text[:497] + "..."
    return text
