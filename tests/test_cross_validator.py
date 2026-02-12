"""Tests for the CrossValidator — bilingual name, URL, and description checks."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scrapers.enrichment.cross_validator import CrossValidator


def _create_products_dir(tmp_path: Path) -> Path:
    """Create a temp products dir with known bilingual entries."""
    products_dir = tmp_path / "products"
    products_dir.mkdir()

    (products_dir / "dou-bao.json").write_text(
        json.dumps({
            "slug": "dou-bao",
            "name": "Doubao",
            "name_zh": "豆包",
            "product_url": "https://www.doubao.com",
            "description": "ByteDance AI assistant for conversation and creative writing",
            "description_zh": "字节跳动推出的AI对话助手，支持多轮对话和创意写作",
            "company": {"name": "ByteDance", "name_zh": "字节跳动"},
        }),
        encoding="utf-8",
    )

    (products_dir / "anthropic.json").write_text(
        json.dumps({
            "slug": "anthropic",
            "name": "Claude",
            "product_url": "https://claude.ai",
            "description": "AI assistant built by Anthropic focused on safety",
            "company": {"name": "Anthropic"},
        }),
        encoding="utf-8",
    )

    (products_dir / "zhipu-ai.json").write_text(
        json.dumps({
            "slug": "zhipu-ai",
            "name": "GLM-4",
            "name_zh": "智谱 AI",
            "description_zh": "智谱AI是一家源自清华大学的AI公司致力于大语言模型研发",
            "company": {
                "name": "Zhipu AI",
                "name_zh": "智谱 AI",
                "headquarters": {"country": "China"},
                "founded_year": 2019,
            },
        }),
        encoding="utf-8",
    )

    return products_dir


def _cv(tmp_path: Path) -> CrossValidator:
    """Create a CrossValidator with patched PRODUCTS_DIR."""
    products_dir = _create_products_dir(tmp_path)
    with patch("scrapers.enrichment.cross_validator.PRODUCTS_DIR", products_dir):
        return CrossValidator()


# -- name_zh collision -------------------------------------------------------


class TestNameZhCollision:
    """Requirement 1: Detect name_zh belonging to another product."""

    def test_rejects_name_zh_owned_by_other(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("anthropic", "name_zh", "豆包") is False
        assert len(cv.violations) == 1
        assert cv.violations[0].conflicting_slug == "dou-bao"

    def test_allows_own_name_zh(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("dou-bao", "name_zh", "豆包") is True
        assert len(cv.violations) == 0

    def test_allows_novel_name_zh(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("anthropic", "name_zh", "克劳德") is True

    def test_rejects_name_zh_matching_english_name(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        # "claude" matches anthropic's English name
        assert cv.validate_field("some-product", "name_zh", "Claude") is False


# -- reverse collision (name vs name_zh) -------------------------------------


class TestReverseCollision:
    """Requirement 2: Detect name matching another's name_zh."""

    def test_rejects_name_matching_other_name_zh(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("new-product", "name", "豆包") is False

    def test_allows_unique_name(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("new-product", "name", "FreshAI") is True


# -- description similarity --------------------------------------------------


class TestDescriptionSimilarity:
    """Requirement 3: Detect near-duplicate descriptions (EN + ZH)."""

    def test_rejects_similar_description_zh(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        similar = "字节跳动推出的AI对话助手，支持多轮对话和创意写作任务"
        assert cv.validate_field("anthropic", "description_zh", similar) is False

    def test_allows_distinct_description_zh(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        distinct = "Anthropic公司推出的安全AI助手，专注于有益和诚实的AI交互"
        assert cv.validate_field("anthropic", "description_zh", distinct) is True

    def test_skips_short_descriptions(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("anthropic", "description_zh", "AI工具") is True

    def test_rejects_similar_english_description(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        similar = "ByteDance AI assistant for conversation and creative writing tasks"
        assert cv.validate_field("anthropic", "description", similar) is False

    def test_allows_distinct_english_description(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        distinct = "A completely different product focused on enterprise analytics"
        assert cv.validate_field("anthropic", "description", distinct) is True


# -- URL cross-validation ---------------------------------------------------


class TestURLValidation:
    """Requirement 4: Detect aggregator URLs and URL collisions."""

    def test_rejects_aggregator_url(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        url = "https://ai-bot.cn/sites/460.html"
        assert cv.validate_field("anthropic", "product_url", url) is False
        assert cv.violations[0].field == "product_url"

    def test_rejects_url_belonging_to_other(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("new-product", "product_url", "https://www.doubao.com") is False

    def test_allows_own_url(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("dou-bao", "product_url", "https://www.doubao.com") is True

    def test_allows_unique_url(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("new-product", "product_url", "https://www.newai.com") is True

    def test_rejects_crunchbase_url(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field(
            "anthropic", "product_url",
            "https://crunchbase.com/organization/anthropic",
        ) is False


# -- within-batch consistency ------------------------------------------------


class TestBatchConsistency:
    """Within-batch index updates prevent collisions across products."""

    def test_batch_collision_after_update(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("product-a", "name_zh", "新名字") is True
        cv.update_index("product-a", "name_zh", "新名字")
        assert cv.validate_field("product-b", "name_zh", "新名字") is False


# -- company consistency (warn-only) ----------------------------------------


class TestCompanyConsistency:
    """Company data consistency checks produce warnings, not rejections."""

    def test_headquarters_mismatch_warns(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        warnings = cv.validate_company_consistency(
            "new-product",
            "Zhipu AI",
            {"headquarters": {"country": "United States"}, "founded_year": 2019},
        )
        assert len(warnings) == 1
        assert "country" in warnings[0].reason
        assert warnings[0].severity == "warning"

    def test_founded_year_mismatch_warns(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        warnings = cv.validate_company_consistency(
            "new-product",
            "Zhipu AI",
            {"headquarters": {"country": "China"}, "founded_year": 2015},
        )
        assert len(warnings) == 1
        assert "founded_year" in warnings[0].reason

    def test_consistent_company_no_warnings(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        warnings = cv.validate_company_consistency(
            "new-product",
            "Zhipu AI",
            {"headquarters": {"country": "China"}, "founded_year": 2019},
        )
        assert len(warnings) == 0


# -- passthrough for non-validated fields ------------------------------------


class TestPassthrough:
    """Non-validated fields always pass through."""

    def test_category_not_validated(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("anthropic", "category", "ai-app") is True

    def test_icon_url_not_validated(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("anthropic", "icon_url", "https://example.com/icon.png") is True

    def test_empty_value_passes(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("anthropic", "name_zh", "") is True

    def test_none_value_passes(self, tmp_path: Path) -> None:
        cv = _cv(tmp_path)
        assert cv.validate_field("anthropic", "name_zh", None) is True
