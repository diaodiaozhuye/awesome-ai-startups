"""LLM-based enrichment for AI product data using Anthropic Claude.

All LLM-generated data is tagged as :attr:`SourceTier.T3_AI_GENERATED`
(trust_score=0.50), meaning :class:`TieredMerger` will only use it to
fill empty fields — existing human-curated or web-scraped data is never
overwritten.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from scrapers.base import ScrapedProduct, SourceTier

logger = logging.getLogger(__name__)

# Fields the LLM is allowed to fill.  These are classification/descriptive
# fields where the LLM can add value without high hallucination risk.
# Factual fields (funding, URLs, employee count, key_people) are excluded.
_ENRICHABLE_FIELDS: dict[str, str] = {
    "description": "description",
    "description_zh": "description_zh",
    "product_type": "product_type",
    "category": "category",
    "sub_category": "sub_category",
    "tags": "tags",
    "modalities": "modalities",
    "platforms": "platforms",
    "target_audience": "target_audience",
    "use_cases": "use_cases",
    "architecture": "architecture",
    "pricing_model": "pricing.model",
    "has_free_tier": "pricing.has_free_tier",
    "open_source": "open_source",
    "api_available": "api_available",
    "competitors": "competitors",
    "status": "status",
}

# Valid enum values (from product.schema.json) for constrained fields.
_VALID_PRODUCT_TYPES = (
    "llm",
    "app",
    "dev-tool",
    "hardware",
    "dataset",
    "framework",
    "api-service",
    "other",
)
_VALID_CATEGORIES = (
    "ai-model",
    "ai-app",
    "ai-dev-tool",
    "ai-infrastructure",
    "ai-hardware",
    "ai-data",
    "ai-agent",
    "ai-search",
    "ai-security",
    "ai-science",
)
_VALID_STATUSES = (
    "active",
    "beta",
    "alpha",
    "announced",
    "deprecated",
    "discontinued",
)
_VALID_PRICING_MODELS = (
    "free",
    "freemium",
    "paid",
    "enterprise",
    "open-source",
    "usage-based",
)

# Default model — fast and cost-effective for classification tasks.
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


def _get_nested(data: dict[str, Any], path: str) -> Any:
    """Retrieve a value from *data* following a dotted *path*."""
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


class LLMEnricher:
    """Enrich product data using Anthropic Claude to fill missing fields.

    Requires the ``ANTHROPIC_API_KEY`` environment variable.

    Usage::

        enricher = LLMEnricher()
        gaps = enricher.identify_gaps(product_dict)
        if gaps:
            scraped = enricher.enrich(product_dict)
            # Feed scraped into TieredMerger
    """

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model
        self._client: Any = None  # Lazy init to avoid import if not needed

    @property
    def client(self) -> Any:
        """Lazily initialise the Anthropic client."""
        if self._client is None:
            try:
                import anthropic  # noqa: F811
            except ImportError as exc:
                raise ImportError(
                    "anthropic package is required for LLM enrichment. "
                    "Install it with: pip install anthropic"
                ) from exc

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is required for LLM enrichment."
                )
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def identify_gaps(self, product: dict[str, Any]) -> list[str]:
        """Return field names that are missing or empty and could be LLM-filled.

        Only considers fields in ``_ENRICHABLE_FIELDS``.
        """
        gaps: list[str] = []
        for field_name, json_path in _ENRICHABLE_FIELDS.items():
            value = _get_nested(product, json_path)
            if value is None or value == "" or value == []:
                gaps.append(field_name)
        return gaps

    def enrich(self, product: dict[str, Any]) -> ScrapedProduct | None:
        """Enrich a single product by asking the LLM to fill missing fields.

        Returns a ``ScrapedProduct`` with T3 tier, or ``None`` if nothing
        to enrich or the LLM call fails.
        """
        gaps = self.identify_gaps(product)
        if not gaps:
            logger.info("No gaps to fill for %s", product.get("slug", "unknown"))
            return None

        prompt = self._build_prompt(product, gaps)
        try:
            response = self._call_llm(prompt)
        except Exception:
            logger.exception("LLM call failed for %s", product.get("slug", "unknown"))
            return None

        parsed = self._parse_response(response, gaps)
        if not parsed:
            return None

        return self._to_scraped_product(product, parsed)

    def _build_prompt(self, product: dict[str, Any], gaps: list[str]) -> str:
        """Build a prompt for the LLM to fill missing fields."""
        # Provide existing context
        context_parts: list[str] = [
            f"Product name: {product.get('name', 'Unknown')}",
        ]
        if product.get("name_zh"):
            context_parts.append(f"Chinese name: {product['name_zh']}")
        if product.get("description"):
            context_parts.append(f"Description: {product['description']}")
        if product.get("product_url"):
            context_parts.append(f"URL: {product['product_url']}")

        company = product.get("company", {})
        if company.get("name"):
            context_parts.append(f"Company: {company['name']}")
        if company.get("headquarters", {}).get("country"):
            context_parts.append(f"Country: {company['headquarters']['country']}")

        if product.get("tags"):
            context_parts.append(f"Existing tags: {', '.join(product['tags'])}")
        if product.get("category"):
            context_parts.append(f"Category: {product['category']}")
        if product.get("product_type"):
            context_parts.append(f"Product type: {product['product_type']}")

        context = "\n".join(context_parts)

        # Build field instructions
        field_instructions: list[str] = []
        for field_name in gaps:
            instruction = self._field_instruction(field_name)
            if instruction:
                field_instructions.append(f'  "{field_name}": {instruction}')

        fields_block = ",\n".join(field_instructions)

        return f"""You are a data analyst enriching an AI product database.
Given the product information below, fill in the missing fields.

PRODUCT CONTEXT:
{context}

INSTRUCTIONS:
- Only fill fields you are confident about based on the product context.
- Use null for fields you are uncertain about.
- For array fields, provide relevant items as JSON arrays.
- Keep descriptions concise and factual.
- For description_zh, translate or write a Chinese description.

Respond with ONLY a valid JSON object containing these fields:
{{
{fields_block}
}}

IMPORTANT: Output ONLY the JSON object, no markdown fencing, no explanation."""

    @staticmethod
    def _field_instruction(field_name: str) -> str:
        """Return type/constraint instructions for a given field."""
        instructions: dict[str, str] = {
            "description": "string (10-200 chars, factual product description)",
            "description_zh": "string (Chinese description, 10-200 chars)",
            "product_type": f"one of {list(_VALID_PRODUCT_TYPES)}",
            "category": f"one of {list(_VALID_CATEGORIES)}",
            "sub_category": 'string (specific sub-category slug, e.g. "text-generation")',
            "tags": "array of strings (3-8 relevant tags, kebab-case)",
            "modalities": (
                'array of strings from: "text", "image", "audio", '
                '"video", "code", "multimodal"'
            ),
            "platforms": (
                'array of strings from: "web", "ios", "android", '
                '"desktop", "api", "cli", "self-hosted"'
            ),
            "target_audience": (
                'array of strings, e.g. ["developers", "enterprises", "researchers"]'
            ),
            "use_cases": (
                'array of strings, e.g. ["code-generation", "chatbot", "content-creation"]'
            ),
            "architecture": 'string (e.g. "transformer", "diffusion", "hybrid")',
            "pricing_model": f"one of {list(_VALID_PRICING_MODELS)}",
            "has_free_tier": "boolean",
            "open_source": "boolean",
            "api_available": "boolean",
            "competitors": 'array of product slugs (kebab-case, e.g. ["chatgpt", "gemini"])',
            "status": f"one of {list(_VALID_STATUSES)}",
        }
        return instructions.get(field_name, "appropriate value")

    def _call_llm(self, prompt: str) -> str:
        """Call the Anthropic API and return the text response."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        # Extract text from the response
        return message.content[0].text

    def _parse_response(self, response: str, gaps: list[str]) -> dict[str, Any] | None:
        """Parse the LLM JSON response and validate fields."""
        # Strip potential markdown fencing
        text = response.strip()
        if text.startswith("```"):
            # Remove ```json ... ``` wrapper
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON: %.200s", text)
            return None

        if not isinstance(data, dict):
            logger.warning("LLM response is not a JSON object")
            return None

        # Validate and clean
        cleaned: dict[str, Any] = {}
        for field_name in gaps:
            value = data.get(field_name)
            if value is None:
                continue
            validated = self._validate_field(field_name, value)
            if validated is not None:
                cleaned[field_name] = validated

        return cleaned if cleaned else None

    @staticmethod
    def _validate_field(field_name: str, value: Any) -> Any:
        """Validate a single field value against schema constraints.

        Returns the validated value or ``None`` if invalid.
        """
        # Enum validations
        if field_name == "product_type":
            return value if value in _VALID_PRODUCT_TYPES else None
        if field_name == "category":
            return value if value in _VALID_CATEGORIES else None
        if field_name == "status":
            return value if value in _VALID_STATUSES else None
        if field_name == "pricing_model":
            return value if value in _VALID_PRICING_MODELS else None

        # Boolean fields
        if field_name in ("has_free_tier", "open_source", "api_available"):
            return value if isinstance(value, bool) else None

        # String fields
        if field_name in (
            "description",
            "description_zh",
            "sub_category",
            "architecture",
        ):
            if isinstance(value, str) and len(value.strip()) >= 2:
                return value.strip()
            return None

        # Array fields
        if field_name in (
            "tags",
            "modalities",
            "platforms",
            "target_audience",
            "use_cases",
            "competitors",
        ):
            if isinstance(value, list):
                # Filter to valid strings only
                items = [
                    str(v).strip() for v in value if isinstance(v, str) and v.strip()
                ]
                return items if items else None
            return None

        return value

    @staticmethod
    def _to_scraped_product(
        product: dict[str, Any], enriched: dict[str, Any]
    ) -> ScrapedProduct:
        """Convert enriched fields into a ``ScrapedProduct`` with T3 tier."""
        # Build kwargs for ScrapedProduct
        kwargs: dict[str, Any] = {
            "name": product.get("name", "Unknown"),
            "source": "llm-enrichment",
            "source_tier": SourceTier.T3_AI_GENERATED,
            "source_url": "",
        }

        # Map enriched fields to ScrapedProduct attributes
        for field_name, value in enriched.items():
            if field_name in ("pricing_model", "has_free_tier"):
                # These map to ScrapedProduct flat fields
                kwargs[field_name] = value
            elif isinstance(value, list):
                # Convert lists to tuples for frozen dataclass
                kwargs[field_name] = tuple(value)
            else:
                kwargs[field_name] = value

        return ScrapedProduct(**kwargs)
