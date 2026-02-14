"""Tests for the TagInferenceEngine rule-based tag inference."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scrapers.enrichment.tag_inference import TagInferenceEngine


@pytest.fixture
def engine() -> TagInferenceEngine:
    return TagInferenceEngine()


def _product(
    name: str = "Test Product",
    description: str = "",
    category: str = "ai-application",
    product_type: str = "app",
    **kwargs: Any,
) -> dict[str, Any]:
    """Build a minimal product dict for testing."""
    data: dict[str, Any] = {
        "slug": "test-product",
        "name": name,
        "description": description,
        "category": category,
        "product_type": product_type,
        "company": {"name": "Test Co", "url": "https://test.co"},
        "sources": [],
        "tags": [],
    }
    data.update(kwargs)
    return data


class TestKeywordMatching:
    """Test regex-based keyword → tag inference from descriptions."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("A transformer-based language model", "transformer"),
            ("Uses diffusion techniques for generation", "diffusion-model"),
            ("RAG-powered knowledge retrieval", "rag"),
            ("Retrieval augmented generation system", "rag"),
            ("Multimodal AI assistant", "multimodal"),
            ("NLP processing engine", "nlp"),
            ("Natural language understanding tool", "nlp"),
            ("Computer vision for manufacturing", "computer-vision"),
            ("Reinforcement learning for robotics", "reinforcement-learning"),
            ("Fine-tuning LLMs on custom data", "fine-tuning"),
            ("Vector embeddings for search", "embedding"),
            ("Speech to text transcription", "speech-to-text"),
            ("Automatic speech recognition (ASR)", "speech-to-text"),
            ("Text to image generation tool", "text-to-image"),
            ("AI image generator", "text-to-image"),
            ("Text to video creation", "text-to-video"),
            ("AI video generator", "text-to-video"),
            ("Text to speech synthesis", "text-to-speech"),
            ("Voice cloning technology", "text-to-speech"),
            ("Code generation assistant", "code-generation"),
            ("Coding assistant for developers", "copilot"),
            ("AI copilot for programming", "copilot"),
            ("AI chatbot for customer service", "chatbot"),
            ("Conversational AI platform", "chatbot"),
        ],
    )
    def test_technology_and_use_case_keywords(
        self, engine: TagInferenceEngine, text: str, expected: str
    ) -> None:
        product = _product(description=text)
        tags = engine.infer(product)
        assert expected in tags, f"Expected '{expected}' in tags for: {text}"

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Healthcare AI diagnostics", "healthcare"),
            ("Medical imaging platform", "healthcare"),
            ("Drug discovery platform using AI", "drug-discovery"),
            ("Pharmaceutical drug discovery tool", "drug-discovery"),
            ("Autonomous vehicles technology", "autonomous-vehicles"),
            ("Self-driving car system", "autonomous-vehicles"),
            ("AI for gaming experiences", "gaming"),
            ("Defense and military AI", "defense"),
            ("Climate change prediction", "climate-energy"),
            ("Robotics platform", "robotics"),
            ("Humanoid robot design", "humanoid-robot"),
        ],
    )
    def test_domain_keywords(
        self, engine: TagInferenceEngine, text: str, expected: str
    ) -> None:
        product = _product(description=text)
        tags = engine.infer(product)
        assert expected in tags, f"Expected '{expected}' in tags for: {text}"

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Open source LLM toolkit", "open-source"),
            ("SaaS platform for teams", "saas"),
            ("Freemium AI tool", "freemium"),
            ("Self-hosted deployment", "self-hosted"),
            ("Enterprise AI solution", "enterprises"),
            ("Developer tool for building AI apps", "developers"),
        ],
    )
    def test_business_model_keywords(
        self, engine: TagInferenceEngine, text: str, expected: str
    ) -> None:
        product = _product(description=text)
        tags = engine.infer(product)
        assert expected in tags, f"Expected '{expected}' in tags for: {text}"


class TestCategoryBasedTags:
    """Test category → default tag mappings."""

    @pytest.mark.parametrize(
        "category,expected_tags",
        [
            ("ai-foundation-model", {"nlp", "researchers"}),
            ("ai-application", {"consumers"}),
            ("ai-creative-media", {"creators", "content-creation"}),
            ("ai-dev-platform", {"developers"}),
            ("ai-infrastructure", {"developers", "enterprises"}),
            ("ai-data-platform", {"data-analysis", "data-scientists"}),
            ("ai-search-retrieval", {"search-engine"}),
            ("ai-hardware", {"robotics"}),
            ("ai-enterprise-vertical", {"enterprises", "b2b"}),
        ],
    )
    def test_category_default_tags(
        self,
        engine: TagInferenceEngine,
        category: str,
        expected_tags: set[str],
    ) -> None:
        product = _product(category=category, description="Minimal desc")
        tags = set(engine.infer(product))
        assert expected_tags.issubset(
            tags
        ), f"Expected {expected_tags} to be subset of {tags} for category {category}"


class TestProductTypeTags:
    """Test product_type → audience tag mappings."""

    @pytest.mark.parametrize(
        "ptype,expected",
        [
            ("model", {"researchers", "developers"}),
            ("library", {"developers", "sdk"}),
            ("api", {"developers", "api-service", "api-platform"}),
            ("dataset", {"researchers", "data-scientists"}),
        ],
    )
    def test_product_type_tags(
        self,
        engine: TagInferenceEngine,
        ptype: str,
        expected: set[str],
    ) -> None:
        product = _product(product_type=ptype, description="Minimal desc")
        tags = set(engine.infer(product))
        assert expected.issubset(tags)


class TestStructuredFieldInference:
    """Test inference from structured (non-text) fields."""

    def test_open_source_true(self, engine: TagInferenceEngine) -> None:
        product = _product(open_source=True, description="Minimal desc")
        assert "open-source" in engine.infer(product)

    def test_open_source_false(self, engine: TagInferenceEngine) -> None:
        product = _product(open_source=False, description="Minimal desc")
        tags = engine.infer(product)
        assert "closed-source" in tags

    def test_repository_url_implies_open_source(
        self, engine: TagInferenceEngine
    ) -> None:
        product = _product(
            repository_url="https://github.com/test/repo", description="Minimal desc"
        )
        assert "open-source" in engine.infer(product)

    def test_api_available(self, engine: TagInferenceEngine) -> None:
        product = _product(api_available=True, description="Minimal desc")
        assert "api-service" in engine.infer(product)

    def test_multimodal_from_modalities(self, engine: TagInferenceEngine) -> None:
        product = _product(
            modalities=["text", "image", "audio"], description="Minimal desc"
        )
        assert "multimodal" in engine.infer(product)

    def test_single_modality_not_multimodal(self, engine: TagInferenceEngine) -> None:
        product = _product(modalities=["text"], description="Minimal desc")
        assert "multimodal" not in engine.infer(product)

    def test_architecture_transformer(self, engine: TagInferenceEngine) -> None:
        product = _product(architecture="Transformer-based", description="Minimal desc")
        assert "transformer" in engine.infer(product)

    def test_architecture_moe(self, engine: TagInferenceEngine) -> None:
        product = _product(
            architecture="Mixture of Experts", description="Minimal desc"
        )
        assert "moe" in engine.infer(product)

    def test_pricing_freemium(self, engine: TagInferenceEngine) -> None:
        product = _product(pricing={"model": "freemium"}, description="Minimal desc")
        assert "freemium" in engine.infer(product)


class TestCountryTags:
    """Test country-based special tags."""

    @pytest.mark.parametrize(
        "country,expected_tag",
        [
            ("China", "china"),
            ("United States", "us"),
            ("Japan", "japan"),
            ("South Korea", "korea"),
            ("United Kingdom", "europe"),
            ("Germany", "europe"),
            ("France", "europe"),
        ],
    )
    def test_country_tags(
        self, engine: TagInferenceEngine, country: str, expected_tag: str
    ) -> None:
        product = _product(
            description="Minimal desc",
            company={
                "name": "Test Co",
                "url": "https://test.co",
                "headquarters": {"country": country},
            },
        )
        assert expected_tag in engine.infer(product)

    def test_unicorn_from_valuation(self, engine: TagInferenceEngine) -> None:
        product = _product(
            description="Minimal desc",
            company={
                "name": "Big Co",
                "url": "https://big.co",
                "funding": {"valuation_usd": 2_000_000_000},
            },
        )
        tags = engine.infer(product)
        assert "unicorn" in tags
        assert "decacorn" not in tags

    def test_decacorn_from_valuation(self, engine: TagInferenceEngine) -> None:
        product = _product(
            description="Minimal desc",
            company={
                "name": "Huge Co",
                "url": "https://huge.co",
                "funding": {"valuation_usd": 15_000_000_000},
            },
        )
        tags = engine.infer(product)
        assert "decacorn" in tags
        assert "unicorn" not in tags


class TestMutualExclusion:
    """Test mutual exclusion logic between conflicting tags."""

    def test_closed_source_removes_open_source_from_text(
        self, engine: TagInferenceEngine
    ) -> None:
        """When open_source=False but description mentions 'open source',
        the closed-source tag should win and open-source should be removed."""
        product = _product(
            open_source=False,
            description="Better than open source alternatives",
        )
        tags = engine.infer(product)
        assert "closed-source" in tags
        assert "open-source" not in tags

    def test_explicit_open_source_kept(self, engine: TagInferenceEngine) -> None:
        product = _product(
            open_source=True,
            description="An open source AI tool",
        )
        tags = engine.infer(product)
        assert "open-source" in tags
        assert "closed-source" not in tags


class TestEdgeCases:
    """Test edge cases and robustness."""

    def test_empty_product(self, engine: TagInferenceEngine) -> None:
        product: dict[str, Any] = {
            "slug": "empty",
            "name": "",
            "description": "",
            "category": "",
            "product_type": "",
            "company": {},
            "sources": [],
            "tags": [],
        }
        tags = engine.infer(product)
        assert isinstance(tags, list)
        assert len(tags) >= 0

    def test_preserves_existing_tags(self, engine: TagInferenceEngine) -> None:
        product = _product(
            description="A basic tool",
            tags=["transformer", "rag"],
        )
        tags = engine.infer(product)
        assert "transformer" in tags
        assert "rag" in tags

    def test_no_duplicate_tags(self, engine: TagInferenceEngine) -> None:
        product = _product(
            description="Transformer-based NLP chatbot with transformer architecture",
            architecture="Transformer",
            tags=["transformer"],
        )
        tags = engine.infer(product)
        assert tags.count("transformer") == 1

    def test_max_tags_cap(self, engine: TagInferenceEngine) -> None:
        """Products with many matching rules should not exceed MAX_TAGS."""
        product = _product(
            description=(
                "Open source transformer NLP chatbot copilot with code generation, "
                "multimodal RAG, diffusion model, text to image, text to video, "
                "speech to text, voice assistant, data analysis, marketing, "
                "healthcare, drug discovery, gaming, robotics, education, "
                "real-time API service SaaS enterprise developer tool"
            ),
            open_source=True,
            api_available=True,
            modalities=["text", "image", "audio", "video"],
            architecture="Transformer MoE",
        )
        tags = engine.infer(product)
        assert len(tags) <= 20

    def test_only_valid_tags_returned(self, engine: TagInferenceEngine) -> None:
        """No invented tags — all must be in tags.json vocabulary."""
        import json

        tags_file = Path(__file__).resolve().parent.parent / "data" / "tags.json"
        valid_ids: set[str] = set()
        data = json.loads(tags_file.read_text(encoding="utf-8"))
        for dim in data["dimensions"].values():
            for tag in dim["tags"]:
                valid_ids.add(tag["id"])

        product = _product(
            description="A comprehensive AI platform for everything",
            open_source=True,
            api_available=True,
        )
        tags = engine.infer(product)
        for tag in tags:
            assert tag in valid_ids, f"Tag '{tag}' not in valid vocabulary"

    def test_redos_resistance(self, engine: TagInferenceEngine) -> None:
        """Ensure bounded regex patterns don't hang on adversarial input."""
        import time

        malicious = "design " + "x " * 5000 + " end"
        product = _product(description=malicious)

        start = time.monotonic()
        engine.infer(product)
        elapsed = time.monotonic() - start

        assert elapsed < 2.0, f"Tag inference took {elapsed:.1f}s — possible ReDoS"
