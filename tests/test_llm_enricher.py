"""Tests for the LLM enricher with mocked Anthropic API."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from scrapers.base import SourceTier
from scrapers.enrichment.llm_enricher import (
    _ENRICHABLE_FIELDS,
    _VALID_CATEGORIES,
    _VALID_PRICING_MODELS,
    _VALID_PRODUCT_TYPES,
    _VALID_STATUSES,
    DEFAULT_MODEL,
    LLMEnricher,
    _get_nested,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SPARSE_PRODUCT: dict = {
    "slug": "test-product",
    "name": "TestAI",
    "product_url": "https://testai.com",
    "description": "An AI product for testing.",
    "product_type": "app",
    "category": "ai-app",
    "status": "active",
    "company": {
        "name": "TestCo",
        "url": "https://testco.com",
    },
    "meta": {"added_date": "2025-01-01"},
}

_FULL_PRODUCT: dict = {
    "slug": "full-product",
    "name": "FullAI",
    "product_url": "https://fullai.com",
    "description": "A fully described AI product.",
    "description_zh": "一个完整描述的 AI 产品。",
    "product_type": "llm",
    "category": "ai-model",
    "sub_category": "text-generation",
    "status": "active",
    "tags": ["generative-ai"],
    "modalities": ["text"],
    "platforms": ["web", "api"],
    "target_audience": ["developers"],
    "use_cases": ["chatbot"],
    "architecture": "transformer",
    "open_source": False,
    "api_available": True,
    "competitors": ["chatgpt"],
    "pricing": {"model": "freemium", "has_free_tier": True},
    "company": {"name": "FullCo", "url": "https://fullco.com"},
}


# ---------------------------------------------------------------------------
# _get_nested
# ---------------------------------------------------------------------------


class TestGetNested:
    def test_simple_key(self) -> None:
        assert _get_nested({"a": 1}, "a") == 1

    def test_dotted_path(self) -> None:
        assert _get_nested({"a": {"b": {"c": 3}}}, "a.b.c") == 3

    def test_missing_key(self) -> None:
        assert _get_nested({"a": 1}, "b") is None

    def test_missing_intermediate(self) -> None:
        assert _get_nested({"a": 1}, "a.b.c") is None

    def test_empty_dict(self) -> None:
        assert _get_nested({}, "a") is None


# ---------------------------------------------------------------------------
# identify_gaps
# ---------------------------------------------------------------------------


class TestIdentifyGaps:
    def test_sparse_product_has_gaps(self) -> None:
        enricher = LLMEnricher()
        gaps = enricher.identify_gaps(_SPARSE_PRODUCT)
        # Missing: description_zh, sub_category, tags, modalities, platforms, etc.
        assert "description_zh" in gaps
        assert "sub_category" in gaps
        assert "tags" in gaps
        assert "modalities" in gaps

    def test_full_product_no_gaps(self) -> None:
        enricher = LLMEnricher()
        gaps = enricher.identify_gaps(_FULL_PRODUCT)
        assert gaps == []

    def test_present_fields_excluded(self) -> None:
        enricher = LLMEnricher()
        gaps = enricher.identify_gaps(_SPARSE_PRODUCT)
        # These are present in _SPARSE_PRODUCT
        assert "description" not in gaps
        assert "product_type" not in gaps
        assert "category" not in gaps
        assert "status" not in gaps

    def test_empty_list_counted_as_gap(self) -> None:
        product = {**_SPARSE_PRODUCT, "tags": []}
        enricher = LLMEnricher()
        gaps = enricher.identify_gaps(product)
        assert "tags" in gaps

    def test_empty_string_counted_as_gap(self) -> None:
        product = {**_SPARSE_PRODUCT, "description": ""}
        enricher = LLMEnricher()
        gaps = enricher.identify_gaps(product)
        assert "description" in gaps


# ---------------------------------------------------------------------------
# _validate_field
# ---------------------------------------------------------------------------


class TestValidateField:
    def test_valid_product_type(self) -> None:
        assert LLMEnricher._validate_field("product_type", "llm") == "llm"

    def test_invalid_product_type(self) -> None:
        assert LLMEnricher._validate_field("product_type", "invalid") is None

    def test_valid_category(self) -> None:
        assert LLMEnricher._validate_field("category", "ai-model") == "ai-model"

    def test_invalid_category(self) -> None:
        assert LLMEnricher._validate_field("category", "bad") is None

    def test_valid_status(self) -> None:
        assert LLMEnricher._validate_field("status", "beta") == "beta"

    def test_invalid_status(self) -> None:
        assert LLMEnricher._validate_field("status", "unknown") is None

    def test_valid_pricing_model(self) -> None:
        assert LLMEnricher._validate_field("pricing_model", "freemium") == "freemium"

    def test_invalid_pricing_model(self) -> None:
        assert LLMEnricher._validate_field("pricing_model", "custom") is None

    def test_boolean_field_true(self) -> None:
        assert LLMEnricher._validate_field("open_source", True) is True

    def test_boolean_field_false(self) -> None:
        assert LLMEnricher._validate_field("open_source", False) is False

    def test_boolean_field_non_bool(self) -> None:
        assert LLMEnricher._validate_field("open_source", "yes") is None

    def test_string_field_valid(self) -> None:
        result = LLMEnricher._validate_field("description", "A valid description")
        assert result == "A valid description"

    def test_string_field_too_short(self) -> None:
        assert LLMEnricher._validate_field("description", "x") is None

    def test_string_field_empty(self) -> None:
        assert LLMEnricher._validate_field("description", "") is None

    def test_string_field_strips(self) -> None:
        assert LLMEnricher._validate_field("architecture", "  transformer  ") == "transformer"

    def test_array_field_valid(self) -> None:
        result = LLMEnricher._validate_field("tags", ["ai", "ml", "nlp"])
        assert result == ["ai", "ml", "nlp"]

    def test_array_field_filters_non_strings(self) -> None:
        result = LLMEnricher._validate_field("tags", ["ai", 123, None, "ml"])
        assert result == ["ai", "ml"]

    def test_array_field_empty(self) -> None:
        assert LLMEnricher._validate_field("tags", []) is None

    def test_array_field_all_invalid(self) -> None:
        assert LLMEnricher._validate_field("tags", [123, None]) is None

    def test_array_field_not_list(self) -> None:
        assert LLMEnricher._validate_field("tags", "not-a-list") is None


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_valid_json(self) -> None:
        enricher = LLMEnricher()
        response = json.dumps({
            "tags": ["ai", "ml"],
            "open_source": True,
        })
        result = enricher._parse_response(response, ["tags", "open_source"])
        assert result == {"tags": ["ai", "ml"], "open_source": True}

    def test_json_with_markdown_fencing(self) -> None:
        enricher = LLMEnricher()
        response = '```json\n{"tags": ["ai"]}\n```'
        result = enricher._parse_response(response, ["tags"])
        assert result == {"tags": ["ai"]}

    def test_invalid_json(self) -> None:
        enricher = LLMEnricher()
        result = enricher._parse_response("not json at all", ["tags"])
        assert result is None

    def test_non_dict_json(self) -> None:
        enricher = LLMEnricher()
        result = enricher._parse_response("[1, 2, 3]", ["tags"])
        assert result is None

    def test_null_values_skipped(self) -> None:
        enricher = LLMEnricher()
        response = json.dumps({"tags": ["ai"], "description": None})
        result = enricher._parse_response(response, ["tags", "description"])
        assert result == {"tags": ["ai"]}

    def test_invalid_values_filtered(self) -> None:
        enricher = LLMEnricher()
        response = json.dumps({
            "product_type": "invalid-type",
            "status": "active",
        })
        result = enricher._parse_response(
            response, ["product_type", "status"]
        )
        assert result == {"status": "active"}

    def test_all_invalid_returns_none(self) -> None:
        enricher = LLMEnricher()
        response = json.dumps({"product_type": "bad", "category": "bad"})
        result = enricher._parse_response(response, ["product_type", "category"])
        assert result is None

    def test_only_requested_gaps_included(self) -> None:
        enricher = LLMEnricher()
        response = json.dumps({
            "tags": ["ai"],
            "extra_field": "ignored",
        })
        result = enricher._parse_response(response, ["tags"])
        assert result == {"tags": ["ai"]}
        assert "extra_field" not in result


# ---------------------------------------------------------------------------
# _build_prompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    def test_includes_product_name(self) -> None:
        enricher = LLMEnricher()
        prompt = enricher._build_prompt(_SPARSE_PRODUCT, ["tags"])
        assert "TestAI" in prompt

    def test_includes_company_name(self) -> None:
        enricher = LLMEnricher()
        prompt = enricher._build_prompt(_SPARSE_PRODUCT, ["tags"])
        assert "TestCo" in prompt

    def test_includes_field_instructions(self) -> None:
        enricher = LLMEnricher()
        prompt = enricher._build_prompt(_SPARSE_PRODUCT, ["product_type", "tags"])
        assert '"product_type"' in prompt
        assert '"tags"' in prompt

    def test_includes_existing_tags(self) -> None:
        product = {**_SPARSE_PRODUCT, "tags": ["ai", "ml"]}
        enricher = LLMEnricher()
        prompt = enricher._build_prompt(product, ["description_zh"])
        assert "ai, ml" in prompt

    def test_includes_chinese_name(self) -> None:
        product = {**_SPARSE_PRODUCT, "name_zh": "测试AI"}
        enricher = LLMEnricher()
        prompt = enricher._build_prompt(product, ["tags"])
        assert "测试AI" in prompt


# ---------------------------------------------------------------------------
# _to_scraped_product
# ---------------------------------------------------------------------------


class TestToScrapedProduct:
    def test_basic_conversion(self) -> None:
        enriched = {"tags": ["ai", "ml"], "open_source": True}
        result = LLMEnricher._to_scraped_product(_SPARSE_PRODUCT, enriched)
        assert result.name == "TestAI"
        assert result.source == "llm-enrichment"
        assert result.source_tier == SourceTier.T3_AI_GENERATED
        assert result.tags == ("ai", "ml")
        assert result.open_source is True

    def test_lists_converted_to_tuples(self) -> None:
        enriched = {"platforms": ["web", "api"]}
        result = LLMEnricher._to_scraped_product(_SPARSE_PRODUCT, enriched)
        assert result.platforms == ("web", "api")
        assert isinstance(result.platforms, tuple)

    def test_scalar_fields(self) -> None:
        enriched = {"description_zh": "描述", "architecture": "transformer"}
        result = LLMEnricher._to_scraped_product(_SPARSE_PRODUCT, enriched)
        assert result.description_zh == "描述"
        assert result.architecture == "transformer"


# ---------------------------------------------------------------------------
# enrich (full flow with mocked LLM)
# ---------------------------------------------------------------------------


class TestEnrich:
    def _make_enricher_with_mock(self, response_json: dict) -> LLMEnricher:
        """Create an enricher with a mocked LLM call."""
        enricher = LLMEnricher()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(response_json))]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        enricher._client = mock_client
        return enricher

    def test_enriches_sparse_product(self) -> None:
        llm_response = {
            "description_zh": "一个用于测试的 AI 产品。",
            "tags": ["ai", "testing"],
            "modalities": ["text"],
            "open_source": False,
        }
        enricher = self._make_enricher_with_mock(llm_response)
        result = enricher.enrich(_SPARSE_PRODUCT)
        assert result is not None
        assert result.source_tier == SourceTier.T3_AI_GENERATED
        assert result.description_zh == "一个用于测试的 AI 产品。"
        assert result.tags == ("ai", "testing")

    def test_returns_none_for_full_product(self) -> None:
        enricher = LLMEnricher()
        enricher._client = MagicMock()
        result = enricher.enrich(_FULL_PRODUCT)
        assert result is None

    def test_returns_none_on_network_error(self) -> None:
        enricher = LLMEnricher()
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = ConnectionError("Connection refused")
        enricher._client = mock_client
        result = enricher.enrich(_SPARSE_PRODUCT)
        assert result is None

    def test_raises_on_unexpected_error(self) -> None:
        enricher = LLMEnricher()
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("Unexpected error")
        enricher._client = mock_client
        with pytest.raises(RuntimeError, match="Unexpected error"):
            enricher.enrich(_SPARSE_PRODUCT)

    def test_returns_none_on_invalid_response(self) -> None:
        enricher = LLMEnricher()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="not json")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        enricher._client = mock_client
        result = enricher.enrich(_SPARSE_PRODUCT)
        assert result is None

    def test_calls_api_with_correct_model(self) -> None:
        enricher = self._make_enricher_with_mock({"tags": ["ai"]})
        enricher.enrich(_SPARSE_PRODUCT)
        call_kwargs = enricher._client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == DEFAULT_MODEL

    def test_custom_model(self) -> None:
        enricher = LLMEnricher(model="claude-haiku-4-5-20251001")
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='{"tags": ["ai"]}')]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        enricher._client = mock_client
        enricher.enrich(_SPARSE_PRODUCT)
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# Client initialization
# ---------------------------------------------------------------------------


class TestClientInit:
    def test_raises_without_api_key(self) -> None:
        mock_anthropic = MagicMock()
        enricher = LLMEnricher()
        enricher._client = None
        with (
            patch.dict("os.environ", {}, clear=True),
            patch.dict("sys.modules", {"anthropic": mock_anthropic}),
            pytest.raises(ValueError, match="ANTHROPIC_API_KEY"),
        ):
            _ = enricher.client

    def test_raises_without_anthropic_package(self) -> None:
        enricher = LLMEnricher()
        enricher._client = None
        with patch.dict(
            "sys.modules", {"anthropic": None}
        ), pytest.raises(ImportError, match="anthropic"):
            _ = enricher.client

    def test_initialises_with_api_key(self) -> None:
        mock_anthropic = MagicMock()
        enricher = LLMEnricher()
        enricher._client = None
        with (
            patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=True),
            patch.dict("sys.modules", {"anthropic": mock_anthropic}),
        ):
            client = enricher.client
            assert client is not None
            mock_anthropic.Anthropic.assert_called_once_with(api_key="test-key")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_enrichable_fields_non_empty(self) -> None:
        assert len(_ENRICHABLE_FIELDS) > 10

    def test_valid_enums_non_empty(self) -> None:
        assert len(_VALID_PRODUCT_TYPES) >= 5
        assert len(_VALID_CATEGORIES) >= 5
        assert len(_VALID_STATUSES) >= 4
        assert len(_VALID_PRICING_MODELS) >= 4

    def test_default_model(self) -> None:
        assert "claude" in DEFAULT_MODEL

    def test_field_instruction_returns_for_all(self) -> None:
        for field_name in _ENRICHABLE_FIELDS:
            result = LLMEnricher._field_instruction(field_name)
            assert isinstance(result, str)
            assert len(result) > 0
