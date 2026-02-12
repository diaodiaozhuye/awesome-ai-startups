"""OpenRouter API scraper for AI model pricing and availability.

T2 Open Web source — provides up-to-date pricing, context window sizes,
and availability status for LLMs accessible through the OpenRouter gateway.
"""

from __future__ import annotations

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.utils import create_http_client

# OpenRouter public API — no auth required for model listing
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Known model ID prefix -> organization mapping
_PREFIX_TO_ORG: dict[str, str] = {
    "openai/": "OpenAI",
    "anthropic/": "Anthropic",
    "google/": "Google",
    "meta-llama/": "Meta",
    "mistralai/": "Mistral AI",
    "deepseek/": "DeepSeek",
    "cohere/": "Cohere",
    "microsoft/": "Microsoft",
    "qwen/": "Alibaba Cloud",
    "01-ai/": "01.AI",
    "databricks/": "Databricks",
    "nvidia/": "NVIDIA",
    "amazon/": "Amazon",
    "perplexity/": "Perplexity",
    "x-ai/": "xAI",
    "nousresearch/": "Nous Research",
}


def _guess_org(model_id: str) -> str | None:
    """Guess organization from the OpenRouter model ID prefix."""
    lower = model_id.lower()
    for prefix, org in _PREFIX_TO_ORG.items():
        if lower.startswith(prefix):
            return org
    return None


def _extract_model_name(model_id: str) -> str:
    """Extract the model name from an OpenRouter model ID like 'openai/gpt-4o'."""
    parts = model_id.split("/", 1)
    return parts[-1] if parts else model_id


def _format_price(price_str: str | None) -> float | None:
    """Convert OpenRouter price string to float, or None."""
    if price_str is None:
        return None
    try:
        val = float(price_str)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None


def _determine_pricing_model(
    input_price: float | None,
    output_price: float | None,
) -> str:
    """Determine the pricing model from price values."""
    if input_price is None and output_price is None:
        return "free"
    if input_price == 0 and output_price == 0:
        return "free"
    return "usage-based"


class OpenRouterScraper(BaseScraper):
    """Scrape OpenRouter for AI model pricing and availability.

    OpenRouter aggregates many LLM providers and exposes a unified API.
    The /models endpoint is public and returns pricing, context windows,
    and modality information for all available models.
    """

    @property
    def source_name(self) -> str:
        return "openrouter"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Fetch model list from OpenRouter and return ScrapedProduct list."""
        client = create_http_client(timeout=30)
        products: list[ScrapedProduct] = []

        try:
            response = client.get(OPENROUTER_MODELS_URL)

            if not response.is_success:
                return products

            data = response.json()
            models = data.get("data", [])

            for model_data in models:
                product = self._parse_model(model_data)
                if product:
                    products.append(product)

                if len(products) >= limit:
                    break

        finally:
            client.close()

        return products

    def _parse_model(self, data: dict) -> ScrapedProduct | None:
        """Parse an OpenRouter model entry into a ScrapedProduct."""
        model_id = data.get("id", "")
        if not model_id:
            return None

        model_name = _extract_model_name(model_id)
        if not model_name:
            return None

        # Pricing — OpenRouter returns per-token prices, we convert to per-1M
        pricing = data.get("pricing", {})
        prompt_price = _format_price(pricing.get("prompt"))
        completion_price = _format_price(pricing.get("completion"))

        # Convert from per-token to per-1M tokens
        input_per_1m = prompt_price * 1_000_000 if prompt_price else None
        output_per_1m = completion_price * 1_000_000 if completion_price else None

        pricing_model = _determine_pricing_model(prompt_price, completion_price)

        # Context window
        context_length = data.get("context_length")

        # Organization
        company_name = _guess_org(model_id)

        # Modalities
        architecture = data.get("architecture", {})
        modality = architecture.get("modality", "")
        modalities = _parse_modalities(modality)

        # Build extra dict with detailed pricing
        extra: dict[str, str] = {
            "openrouter_id": model_id,
        }
        if input_per_1m is not None:
            extra["input_price_per_1m_tokens"] = f"{input_per_1m:.4f}"
        if output_per_1m is not None:
            extra["output_price_per_1m_tokens"] = f"{output_per_1m:.4f}"

        return ScrapedProduct(
            name=model_name,
            source="openrouter",
            source_url=f"https://openrouter.ai/models/{model_id}",
            source_tier=SourceTier.T2_OPEN_WEB,
            product_url=f"https://openrouter.ai/models/{model_id}",
            description=data.get("description")
            or f"{model_name} available on OpenRouter.",
            product_type="llm",
            category="ai-model",
            sub_category="text-generation",
            tags=("llm", "api-service"),
            modalities=tuple(modalities),
            context_window=context_length,
            company_name=company_name,
            pricing_model=pricing_model,
            has_free_tier=pricing_model == "free",
            api_available=True,
            api_docs_url="https://openrouter.ai/docs",
            status="active",
            extra=extra,
        )


def _parse_modalities(modality_str: str) -> list[str]:
    """Parse OpenRouter modality string like 'text->text' into modality list."""
    if not modality_str:
        return ["text"]

    parts = set()
    for segment in modality_str.replace("->", "+").split("+"):
        segment = segment.strip().lower()
        if segment in ("text", "image", "audio", "video"):
            parts.add(segment)

    return sorted(parts) if parts else ["text"]
