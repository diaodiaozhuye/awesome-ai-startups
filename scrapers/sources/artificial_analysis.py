"""Artificial Analysis scraper via Firecrawl.

T2 Open Web — scrapes artificialanalysis.ai for AI model performance
benchmarks including speed (tokens/sec), pricing, and quality scores.
Provides complementary data to LMSYS Arena and OpenRouter.
"""

from __future__ import annotations

import logging
import re

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier

logger = logging.getLogger(__name__)

_BASE_URL = "https://artificialanalysis.ai"

# Pages to scrape for model performance data
_SCRAPE_PAGES = [
    "/leaderboards/models",
    "/leaderboards/hardware",
]

# Regex for model performance table rows
# Format: | Model | Provider | Quality | Speed | Price | Context |
_MODEL_ROW_PATTERN = re.compile(
    r"\|\s*\[?([^\]|]{2,60})\]?"
    r"(?:\([^)]*\))?\s*\|"
    r"\s*([^|]{1,40})\s*\|"  # provider
    r"\s*([0-9]+\.?[0-9]*)\s*\|"  # quality score
    r"\s*([0-9,]+\.?[0-9]*)\s*\|"  # speed (tokens/sec)
    r"\s*\$?([0-9]+\.?[0-9]*)\s*\|",  # price
    re.MULTILINE,
)

# Simpler pattern for model entries with name + metrics
_MODEL_SIMPLE_PATTERN = re.compile(
    r"(?:^|\n)"
    r"(?:\d+[\.\)]\s*)?"
    r"\[?([A-Za-z][^\]\n|]{2,60})\]?"
    r"(?:\([^)]*\))?\s*"
    r"[|:]\s*"
    r".*?"
    r"(\d+\.?\d*)\s*(?:tok(?:en)?s?/s|t/s|tokens per second)",
    re.MULTILINE | re.IGNORECASE,
)

# Known provider mappings
_PROVIDER_MAP: dict[str, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google DeepMind",
    "meta": "Meta",
    "mistral": "Mistral AI",
    "cohere": "Cohere",
    "deepseek": "DeepSeek",
    "alibaba": "Alibaba",
    "01.ai": "01.AI",
    "microsoft": "Microsoft",
    "amazon": "Amazon",
    "nvidia": "NVIDIA",
    "together": "Together AI",
    "anyscale": "Anyscale",
    "groq": "Groq",
    "fireworks": "Fireworks AI",
}


class ArtificialAnalysisScraper(BaseScraper):
    """Scrape Artificial Analysis for AI model performance data.

    Extracts model speed, pricing, and quality benchmark data
    via Firecrawl. Enriches products with performance metrics
    stored in the extra field.
    """

    @property
    def source_name(self) -> str:
        return "artificial_analysis"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape Artificial Analysis leaderboard pages."""
        try:
            from scrapers.utils.firecrawl_client import FirecrawlClient
        except ImportError:
            logger.info("Firecrawl not available, skipping Artificial Analysis.")
            return []

        fc = FirecrawlClient()
        products: list[ScrapedProduct] = []
        seen_names: set[str] = set()

        try:
            for page_path in _SCRAPE_PAGES:
                if fc.remaining_quota <= 0:
                    logger.warning("Firecrawl quota exhausted.")
                    break

                url = f"{_BASE_URL}{page_path}"
                logger.debug("ArtificialAnalysis: scraping %s", page_path)

                result = fc.scrape_url(url, formats=["markdown"], wait_for=5000)

                if not result.success:
                    logger.debug("ArtificialAnalysis failed: %s", result.error)
                    continue

                parsed = self._parse_leaderboard(result.markdown, url)

                for product in parsed:
                    key = product.name.lower()
                    if key in seen_names:
                        continue
                    seen_names.add(key)
                    products.append(product)

                    if len(products) >= limit:
                        break

        finally:
            fc.close()

        logger.info("ArtificialAnalysis: discovered %d models", len(products))
        return products

    def _parse_leaderboard(self, markdown: str, page_url: str) -> list[ScrapedProduct]:
        """Parse the leaderboard markdown into products."""
        if not markdown or len(markdown) < 100:
            return []

        products: list[ScrapedProduct] = []

        for match in _MODEL_ROW_PATTERN.finditer(markdown):
            name = match.group(1).strip()
            provider = match.group(2).strip()
            quality = match.group(3).strip()
            speed = match.group(4).strip().replace(",", "")
            price = match.group(5).strip()

            if len(name) < 2 or len(name) > 60:
                continue

            org = _normalize_provider(provider)

            extra: dict[str, str] = {}
            if quality:
                extra["aa_quality_score"] = quality
            if speed:
                extra["aa_speed_tokens_per_sec"] = speed
            if price:
                extra["aa_price_per_1m_tokens"] = price

            products.append(
                ScrapedProduct(
                    name=name,
                    source=self.source_name,
                    source_url=page_url,
                    source_tier=SourceTier.T2_OPEN_WEB,
                    product_type="llm",
                    category="ai-model",
                    company_name=org,
                    status="active",
                    extra=extra,
                )
            )

        # Fallback to simpler pattern if table parsing yielded few results
        if len(products) < 3:
            for match in _MODEL_SIMPLE_PATTERN.finditer(markdown):
                name = match.group(1).strip()
                speed = match.group(2).strip()

                if len(name) < 2:
                    continue

                extra = {"aa_speed_tokens_per_sec": speed} if speed else {}

                products.append(
                    ScrapedProduct(
                        name=name,
                        source=self.source_name,
                        source_url=page_url,
                        source_tier=SourceTier.T2_OPEN_WEB,
                        product_type="llm",
                        category="ai-model",
                        company_name=_guess_org_from_name(name),
                        status="active",
                        extra=extra,
                    )
                )

        return products


def _normalize_provider(raw: str) -> str | None:
    """Normalize a provider string to a known company name."""
    if not raw:
        return None
    raw_lower = raw.lower().strip()
    for key, org in _PROVIDER_MAP.items():
        if key in raw_lower:
            return org
    return raw.strip() or None


def _guess_org_from_name(model_name: str) -> str | None:
    """Guess organization from model name prefix."""
    name_lower = model_name.lower()
    prefixes: dict[str, str] = {
        "gpt": "OpenAI",
        "claude": "Anthropic",
        "gemini": "Google DeepMind",
        "llama": "Meta",
        "mistral": "Mistral AI",
        "qwen": "Alibaba",
        "deepseek": "DeepSeek",
        "phi": "Microsoft",
        "command": "Cohere",
    }
    for prefix, org in prefixes.items():
        if name_lower.startswith(prefix):
            return org
    return None
