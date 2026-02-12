"""HuggingFace Hub scraper for AI models and datasets.

T2 Open Web source — provides rich model metadata including architecture,
parameter counts, benchmarks, licenses, and download statistics.
"""

from __future__ import annotations

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.utils import create_http_client

# HuggingFace public API endpoints (no auth required for public models)
HF_API_BASE = "https://huggingface.co/api"
HF_MODELS_URL = f"{HF_API_BASE}/models"

# Tags that indicate AI model categories
_TAG_TO_SUBCATEGORY: dict[str, str] = {
    "text-generation": "text-generation",
    "text2text-generation": "text-generation",
    "text-classification": "text-generation",
    "fill-mask": "text-generation",
    "question-answering": "text-generation",
    "summarization": "text-generation",
    "translation": "text-generation",
    "conversational": "text-generation",
    "image-classification": "image-generation",
    "image-to-text": "image-generation",
    "text-to-image": "image-generation",
    "image-segmentation": "image-generation",
    "object-detection": "image-generation",
    "text-to-video": "video-generation",
    "text-to-audio": "audio-speech",
    "text-to-speech": "audio-speech",
    "automatic-speech-recognition": "audio-speech",
    "audio-classification": "audio-speech",
    "feature-extraction": "embedding",
    "sentence-similarity": "embedding",
    "zero-shot-classification": "multimodal",
    "visual-question-answering": "multimodal",
    "document-question-answering": "multimodal",
    "image-text-to-text": "multimodal",
}

# License mapping: HuggingFace tag -> SPDX identifier
_LICENSE_MAP: dict[str, str] = {
    "apache-2.0": "Apache-2.0",
    "mit": "MIT",
    "gpl-3.0": "GPL-3.0-only",
    "cc-by-4.0": "CC-BY-4.0",
    "cc-by-nc-4.0": "CC-BY-NC-4.0",
    "cc-by-sa-4.0": "CC-BY-SA-4.0",
    "cc-by-nc-sa-4.0": "CC-BY-NC-SA-4.0",
    "openrail": "OpenRAIL",
    "openrail++": "OpenRAIL++",
    "llama2": "Llama-2",
    "llama3": "Llama-3",
    "llama3.1": "Llama-3.1",
    "llama3.2": "Llama-3.2",
    "gemma": "Gemma",
    "bigscience-bloom-rail-1.0": "BLOOM-RAIL-1.0",
}

# Known organization -> company name mapping
_ORG_TO_COMPANY: dict[str, str] = {
    "meta-llama": "Meta",
    "google": "Google",
    "microsoft": "Microsoft",
    "openai": "OpenAI",
    "mistralai": "Mistral AI",
    "Qwen": "Alibaba Cloud",
    "deepseek-ai": "DeepSeek",
    "01-ai": "01.AI",
    "THUDM": "Tsinghua University",
    "bigscience": "BigScience",
    "EleutherAI": "EleutherAI",
    "stabilityai": "Stability AI",
    "black-forest-labs": "Black Forest Labs",
    "HuggingFaceH4": "Hugging Face",
    "tiiuae": "Technology Innovation Institute",
    "NousResearch": "Nous Research",
    "databricks": "Databricks",
    "CohereForAI": "Cohere",
    "allenai": "Allen Institute for AI",
    "BAAI": "Beijing Academy of AI",
}

# Pipeline tag -> product_type mapping
_PIPELINE_TO_PRODUCT_TYPE: dict[str, str] = {
    "text-generation": "llm",
    "text2text-generation": "llm",
    "conversational": "llm",
    "fill-mask": "llm",
    "text-to-image": "other",
    "image-classification": "other",
    "image-to-text": "other",
    "image-segmentation": "other",
    "object-detection": "other",
    "text-to-audio": "other",
    "text-to-speech": "other",
    "automatic-speech-recognition": "other",
    "audio-classification": "other",
    "text-to-video": "other",
    "feature-extraction": "framework",
    "sentence-similarity": "framework",
}


class HuggingFaceScraper(BaseScraper):
    """Scrape HuggingFace Hub for AI model metadata.

    Uses the public HuggingFace API to discover trending and popular
    AI models, extracting rich metadata about architecture, parameters,
    benchmarks, and licensing.
    """

    @property
    def source_name(self) -> str:
        return "huggingface"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Fetch trending/popular models from HuggingFace Hub."""
        client = create_http_client(timeout=30)
        products: list[ScrapedProduct] = []

        try:
            # Fetch models sorted by downloads (most popular)
            response = client.get(
                HF_MODELS_URL,
                params={
                    "sort": "downloads",
                    "direction": "-1",
                    "limit": limit,
                    "full": "true",
                },
            )

            if not response.is_success:
                return products

            models = response.json()

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
        """Parse a HuggingFace model API response into a ScrapedProduct."""
        model_id = data.get("modelId") or data.get("id", "")
        if not model_id:
            return None

        # Split org/model
        parts = model_id.split("/", 1)
        org = parts[0] if len(parts) > 1 else ""
        model_name = parts[-1]

        # Skip if model name looks like a fine-tune tag only
        if not model_name or len(model_name) < 2:
            return None

        # Determine pipeline task and sub_category
        pipeline_tag = data.get("pipeline_tag", "")
        sub_category = _TAG_TO_SUBCATEGORY.get(pipeline_tag)

        # Tags
        hf_tags = data.get("tags", [])
        tags = self._extract_tags(hf_tags, pipeline_tag)

        # Modalities
        modalities = self._extract_modalities(pipeline_tag, hf_tags)

        # License
        license_tag = (
            data.get("cardData", {}).get("license") if data.get("cardData") else None
        )
        if not license_tag:
            # Fallback: check tags
            for tag in hf_tags:
                if tag in _LICENSE_MAP:
                    license_tag = tag
                    break
        spdx_license = _LICENSE_MAP.get(license_tag or "", license_tag)

        # Parameter count
        safetensors = data.get("safetensors")
        param_count = None
        if safetensors and isinstance(safetensors, dict):
            total = safetensors.get("total")
            if total:
                param_count = _format_param_count(total)

        # Downloads
        downloads = data.get("downloads", 0)

        # Company name
        company_name = _ORG_TO_COMPANY.get(org, org) if org else None

        return ScrapedProduct(
            name=model_name,
            source="huggingface",
            source_url=f"https://huggingface.co/{model_id}",
            source_tier=SourceTier.T2_OPEN_WEB,
            product_url=f"https://huggingface.co/{model_id}",
            description=self._build_description(
                model_name, company_name, pipeline_tag, param_count
            ),
            product_type=_PIPELINE_TO_PRODUCT_TYPE.get(pipeline_tag, "other"),
            category="ai-model",
            sub_category=sub_category,
            tags=tuple(tags),
            modalities=tuple(modalities),
            open_source=True,
            license=spdx_license,
            repository_url=f"https://huggingface.co/{model_id}",
            parameter_count=param_count,
            company_name=company_name,
            api_available=True,
            api_docs_url=f"https://huggingface.co/{model_id}#how-to-use",
            status="active",
            extra={
                "huggingface_downloads": str(downloads),
                "huggingface_id": model_id,
                "pipeline_tag": pipeline_tag,
            },
        )

    def _extract_tags(self, hf_tags: list, pipeline_tag: str) -> list[str]:
        """Extract meaningful tags from HuggingFace model tags."""
        tags: list[str] = ["open-source"]
        if pipeline_tag:
            tags.append(pipeline_tag)

        # Pick architecture tags
        arch_tags = {
            "transformer",
            "diffusion",
            "moe",
            "mamba",
            "rwkv",
            "ssm",
            "cnn",
            "gan",
        }
        for tag in hf_tags:
            lower = tag.lower()
            if lower in arch_tags:
                tags.append(lower)

        return tags

    def _extract_modalities(self, pipeline_tag: str, hf_tags: list) -> list[str]:
        """Determine input/output modalities from pipeline tag."""
        modalities: set[str] = set()

        text_tasks = {
            "text-generation",
            "text2text-generation",
            "text-classification",
            "fill-mask",
            "question-answering",
            "summarization",
            "translation",
            "conversational",
            "sentence-similarity",
        }
        image_tasks = {
            "image-classification",
            "image-to-text",
            "text-to-image",
            "image-segmentation",
            "object-detection",
        }
        audio_tasks = {
            "text-to-audio",
            "text-to-speech",
            "automatic-speech-recognition",
            "audio-classification",
        }
        video_tasks = {"text-to-video"}
        code_tasks = {"code-generation"}

        if pipeline_tag in text_tasks:
            modalities.add("text")
        if pipeline_tag in image_tasks:
            modalities.update({"text", "image"})
        if pipeline_tag in audio_tasks:
            modalities.update({"text", "audio"})
        if pipeline_tag in video_tasks:
            modalities.update({"text", "video"})
        if pipeline_tag in code_tasks:
            modalities.update({"text", "code"})
        if pipeline_tag in {"visual-question-answering", "image-text-to-text"}:
            modalities.update({"text", "image"})

        return sorted(modalities)

    def _build_description(
        self,
        model_name: str,
        company: str | None,
        pipeline_tag: str,
        param_count: str | None,
    ) -> str:
        """Build a concise description from model metadata."""
        parts = [model_name]
        if company:
            parts.append(f"by {company}")
        if param_count:
            parts.append(f"({param_count} parameters)")
        if pipeline_tag:
            parts.append(f"— a {pipeline_tag.replace('-', ' ')} model")
        parts.append("on HuggingFace.")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_param_count(total: int) -> str:
    """Format a parameter count into a human-readable string.

    >>> _format_param_count(7_000_000_000)
    '7B'
    >>> _format_param_count(1_500_000_000_000)
    '1.5T'
    >>> _format_param_count(350_000_000)
    '350M'
    """
    if total >= 1_000_000_000_000:
        value = total / 1_000_000_000_000
        return f"{value:.1f}T".replace(".0T", "T")
    if total >= 1_000_000_000:
        value = total / 1_000_000_000
        return f"{value:.1f}B".replace(".0B", "B")
    if total >= 1_000_000:
        value = total / 1_000_000
        return f"{value:.0f}M"
    return str(total)
