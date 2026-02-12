"""LMSYS Chatbot Arena leaderboard scraper.

T2 Open Web source — fetches the most authoritative LLM benchmark
(Elo ratings from Chatbot Arena) via the HuggingFace Dataset API.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.utils import create_http_client

if TYPE_CHECKING:
    import httpx

# The LMSYS leaderboard data is published as a HuggingFace dataset.
# We use the dataset viewer API to fetch rows without needing the
# datasets library installed.
HF_DATASET_API = "https://datasets-server.huggingface.co/rows"
LMSYS_DATASET = "lmsys/chatbot_arena_leaderboard"
LMSYS_CONFIG = "default"
LMSYS_SPLIT = "train"

# Known model name -> organization mapping
_MODEL_ORG_MAP: dict[str, str] = {
    "gpt-4": "OpenAI",
    "gpt-4o": "OpenAI",
    "gpt-4-turbo": "OpenAI",
    "gpt-3.5-turbo": "OpenAI",
    "claude-3": "Anthropic",
    "claude-3-opus": "Anthropic",
    "claude-3-sonnet": "Anthropic",
    "claude-3-haiku": "Anthropic",
    "claude-3.5-sonnet": "Anthropic",
    "claude-2": "Anthropic",
    "gemini-pro": "Google",
    "gemini-ultra": "Google",
    "gemini-1.5-pro": "Google",
    "llama-2": "Meta",
    "llama-3": "Meta",
    "llama-3.1": "Meta",
    "mistral": "Mistral AI",
    "mixtral": "Mistral AI",
    "yi": "01.AI",
    "qwen": "Alibaba Cloud",
    "deepseek": "DeepSeek",
    "command-r": "Cohere",
    "dbrx": "Databricks",
    "phi-3": "Microsoft",
    "phi-4": "Microsoft",
    "wizardlm": "Microsoft",
    "vicuna": "LMSYS",
    "chatglm": "Zhipu AI",
    "glm-4": "Zhipu AI",
    "baichuan": "Baichuan Inc.",
    "internlm": "Shanghai AI Lab",
}


class LMSYSScraper(BaseScraper):
    """Scrape the LMSYS Chatbot Arena leaderboard for LLM benchmark data.

    The Chatbot Arena is widely considered the most reliable human-preference
    LLM benchmark. This scraper fetches Elo ratings and model metadata
    via the HuggingFace Dataset Viewer API.
    """

    @property
    def source_name(self) -> str:
        return "lmsys"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Fetch the LMSYS leaderboard and return ScrapedProduct list."""
        client = create_http_client(timeout=30)
        products: list[ScrapedProduct] = []
        today = date.today().isoformat()

        try:
            rows = self._fetch_leaderboard(client, limit)

            for row_data in rows:
                row = row_data.get("row", row_data)
                product = self._parse_row(row, today)
                if product:
                    products.append(product)

                if len(products) >= limit:
                    break

        finally:
            client.close()

        return products

    def _fetch_leaderboard(
        self,
        client: httpx.Client,  # noqa: F821
        limit: int,
    ) -> list[dict]:
        """Fetch rows from the LMSYS leaderboard dataset."""
        try:
            response = client.get(
                HF_DATASET_API,
                params={
                    "dataset": LMSYS_DATASET,
                    "config": LMSYS_CONFIG,
                    "split": LMSYS_SPLIT,
                    "offset": 0,
                    "length": min(limit, 200),
                },
            )

            if not response.is_success:
                # Fallback: try alternative endpoint format
                return self._fetch_leaderboard_fallback(client, limit)

            data = response.json()
            return data.get("rows", [])

        except Exception:
            return self._fetch_leaderboard_fallback(client, limit)

    def _fetch_leaderboard_fallback(
        self,
        client: httpx.Client,  # noqa: F821
        limit: int,
    ) -> list[dict]:
        """Fallback: try the parquet endpoint or direct API."""
        try:
            # Try the first-rows endpoint
            response = client.get(
                "https://datasets-server.huggingface.co/first-rows",
                params={
                    "dataset": LMSYS_DATASET,
                    "config": LMSYS_CONFIG,
                    "split": LMSYS_SPLIT,
                },
            )

            if not response.is_success:
                return []

            data = response.json()
            return data.get("rows", [])

        except Exception:
            return []

    def _parse_row(self, row: dict, today: str) -> ScrapedProduct | None:
        """Parse a leaderboard row into a ScrapedProduct."""
        # The dataset columns vary but typically include:
        # - key/model_name: Model identifier
        # - elo_rating/arena_score: Elo rating
        # - organization: Company behind the model
        # - license: Model license

        model_name = (
            row.get("key")
            or row.get("model_name")
            or row.get("Model")
            or row.get("model")
            or ""
        )
        if not model_name:
            return None

        # Clean up model name
        model_name = model_name.strip()
        if not model_name:
            return None

        # Elo rating
        elo = (
            row.get("arena_score")
            or row.get("elo_rating")
            or row.get("Arena Elo (Avg)")
            or row.get("rating")
        )

        # Organization
        org = (
            row.get("organization")
            or row.get("Organization")
            or row.get("org")
            or self._guess_org(model_name)
        )

        # License
        model_license = row.get("license") or row.get("License")

        # Build benchmarks dict
        benchmarks: dict[str, str] = {}
        if elo is not None:
            benchmarks["chatbot_arena_elo"] = str(elo)

        # Additional benchmark columns
        for col in ("MT-bench", "MMLU", "coding", "math", "reasoning"):
            val = row.get(col)
            if val is not None:
                benchmarks[col.lower().replace("-", "_")] = str(val)

        return ScrapedProduct(
            name=model_name,
            source="lmsys",
            source_url="https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard",
            source_tier=SourceTier.T2_OPEN_WEB,
            description=f"{model_name} — ranked on the LMSYS Chatbot Arena leaderboard"
            + (f" with Elo rating {elo}" if elo else "")
            + ".",
            product_type="llm",
            category="ai-model",
            sub_category="text-generation",
            tags=("llm", "benchmark", "chatbot-arena"),
            company_name=org,
            open_source=_is_likely_open_source(model_name, model_license),
            license=model_license,
            status="active",
            extra=benchmarks,
        )

    def _guess_org(self, model_name: str) -> str | None:
        """Guess the organization from the model name."""
        name_lower = model_name.lower()
        for prefix, org in _MODEL_ORG_MAP.items():
            if name_lower.startswith(prefix):
                return org
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_likely_open_source(model_name: str, license_str: str | None) -> bool | None:
    """Heuristic: guess if a model is open source."""
    name_lower = model_name.lower()

    # Known proprietary models
    proprietary_prefixes = ("gpt-", "claude-", "gemini-", "o1-", "o3-")
    for prefix in proprietary_prefixes:
        if name_lower.startswith(prefix):
            return False

    # If there's an explicit license, likely open
    if license_str and license_str.lower() not in ("proprietary", "unknown", ""):
        return True

    # Known open-source families
    open_families = (
        "llama",
        "mistral",
        "mixtral",
        "qwen",
        "deepseek",
        "yi-",
        "phi-",
        "vicuna",
        "falcon",
        "mpt-",
        "olmo",
        "gemma",
    )
    for family in open_families:
        if name_lower.startswith(family):
            return True

    return None
