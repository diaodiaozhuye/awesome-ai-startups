"""Tests for the TieredMerger."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from scrapers.base import ScrapedProduct, SourceTier
from scrapers.enrichment.merger import (
    TieredMerger,
    _get_nested,
    _set_nested,
)


@pytest.fixture
def merger() -> TieredMerger:
    return TieredMerger()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_product(**kwargs: Any) -> ScrapedProduct:
    """Create a ScrapedProduct with sensible defaults."""
    defaults: dict[str, Any] = {
        "name": "TestProduct",
        "source": "test",
        "source_url": "https://test.com",
        "source_tier": SourceTier.T2_OPEN_WEB,
        "description": "A test product for unit testing purposes.",
        "product_type": "app",
        "category": "ai-app",
        "status": "active",
        "product_url": "https://test.com",
        "company_name": "TestCo",
        "company_website": "https://testco.com",
    }
    defaults.update(kwargs)
    return ScrapedProduct(**defaults)


def _valid_product_json(slug: str = "test-product") -> dict[str, Any]:
    """Return a minimal valid product JSON dict."""
    return {
        "slug": slug,
        "name": "Test Product",
        "product_url": "https://test.com",
        "description": "A test product for unit testing purposes.",
        "product_type": "app",
        "category": "ai-app",
        "status": "active",
        "company": {"name": "TestCo", "url": "https://testco.com"},
        "sources": [],
        "meta": {
            "added_date": "2026-01-01",
            "last_updated": "2026-01-01",
            "provenance": {},
        },
    }


# ---------------------------------------------------------------------------
# Tests for nested dict helpers
# ---------------------------------------------------------------------------


class TestGetNested:
    def test_simple_path(self) -> None:
        assert _get_nested({"a": 1}, "a") == 1

    def test_nested_path(self) -> None:
        assert _get_nested({"a": {"b": {"c": 3}}}, "a.b.c") == 3

    def test_missing_key(self) -> None:
        assert _get_nested({"a": 1}, "b") is None

    def test_missing_intermediate(self) -> None:
        assert _get_nested({"a": 1}, "a.b.c") is None

    def test_empty_dict(self) -> None:
        assert _get_nested({}, "a") is None


class TestSetNested:
    def test_simple_path(self) -> None:
        d: dict[str, Any] = {}
        _set_nested(d, "a", 1)
        assert d == {"a": 1}

    def test_nested_path(self) -> None:
        d: dict[str, Any] = {}
        _set_nested(d, "a.b.c", 3)
        assert d == {"a": {"b": {"c": 3}}}

    def test_preserves_existing(self) -> None:
        d: dict[str, Any] = {"a": {"x": 1}}
        _set_nested(d, "a.b", 2)
        assert d == {"a": {"x": 1, "b": 2}}


# ---------------------------------------------------------------------------
# Tests for TieredMerger
# ---------------------------------------------------------------------------


class TestCreateNew:
    def test_creates_product_with_required_fields(
        self, merger: TieredMerger, tmp_path: Any
    ) -> None:
        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.create_new(
                "test-product",
                _make_product(),
            )

        assert product["slug"] == "test-product"
        assert product["name"] == "TestProduct"
        assert product["product_type"] == "app"
        assert product["category"] == "ai-app"
        assert product["status"] == "active"
        assert product["company"]["name"] == "TestCo"
        assert product["company"]["url"] == "https://testco.com"

    def test_creates_file_on_disk(self, merger: TieredMerger, tmp_path: Any) -> None:
        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            merger.create_new("test-product", _make_product())

        filepath = tmp_path / "test-product.json"
        assert filepath.exists()
        data = json.loads(filepath.read_text(encoding="utf-8"))
        assert data["slug"] == "test-product"

    def test_includes_meta(self, merger: TieredMerger, tmp_path: Any) -> None:
        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.create_new("test-product", _make_product())

        assert "meta" in product
        assert "added_date" in product["meta"]
        assert "last_updated" in product["meta"]
        assert "provenance" in product["meta"]

    def test_includes_i18n_fields(self, merger: TieredMerger, tmp_path: Any) -> None:
        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.create_new(
                "test-product",
                _make_product(
                    name_zh="测试产品", description_zh="测试描述信息，足够长"
                ),
            )

        assert product["name_zh"] == "测试产品"
        assert product["description_zh"] == "测试描述信息，足够长"

    def test_includes_company_details(
        self, merger: TieredMerger, tmp_path: Any
    ) -> None:
        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.create_new(
                "test-product",
                _make_product(
                    company_founded_year=2020,
                    company_headquarters_city="SF",
                    company_headquarters_country="United States",
                    company_headquarters_country_code="US",
                    company_total_raised_usd=1000000.0,
                    company_employee_count_range="11-50",
                ),
            )

        assert product["company"]["founded_year"] == 2020
        assert product["company"]["headquarters"]["city"] == "SF"
        assert product["company"]["funding"]["total_raised_usd"] == 1000000.0
        assert product["company"]["employee_count_range"] == "11-50"

    def test_includes_tags_and_keywords(
        self, merger: TieredMerger, tmp_path: Any
    ) -> None:
        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.create_new(
                "test-product",
                _make_product(tags=("ai", "nlp"), keywords=("machine-learning",)),
            )

        assert product["tags"] == ["ai", "nlp"]
        assert product["keywords"] == ["machine-learning"]

    def test_includes_sources(self, merger: TieredMerger, tmp_path: Any) -> None:
        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.create_new(
                "test-product",
                _make_product(source_url="https://test.com"),
            )

        assert len(product["sources"]) == 1
        assert product["sources"][0]["url"] == "https://test.com"
        assert product["sources"][0]["source_name"] == "test"


class TestMergeUpdate:
    def test_fills_empty_fields(self, merger: TieredMerger, tmp_path: Any) -> None:
        # Create initial product with minimal data
        filepath = tmp_path / "test-product.json"
        existing = _valid_product_json()
        filepath.write_text(json.dumps(existing), encoding="utf-8")

        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.merge_update(
                "test-product",
                _make_product(
                    company_founded_year=2020,
                    company_headquarters_city="SF",
                ),
            )

        assert product["company"]["founded_year"] == 2020
        assert product["company"]["headquarters"]["city"] == "SF"

    def test_records_provenance(self, merger: TieredMerger, tmp_path: Any) -> None:
        filepath = tmp_path / "test-product.json"
        filepath.write_text(json.dumps(_valid_product_json()), encoding="utf-8")

        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.merge_update(
                "test-product",
                _make_product(company_founded_year=2020),
            )

        prov = product["meta"]["provenance"]
        assert "company.founded_year" in prov
        assert prov["company.founded_year"]["source"] == "test"
        assert prov["company.founded_year"]["tier"] == 2

    def test_extends_array_fields(self, merger: TieredMerger, tmp_path: Any) -> None:
        existing = _valid_product_json()
        existing["tags"] = ["existing-tag"]
        filepath = tmp_path / "test-product.json"
        filepath.write_text(json.dumps(existing), encoding="utf-8")

        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.merge_update(
                "test-product",
                _make_product(tags=("new-tag", "existing-tag")),
            )

        assert "existing-tag" in product["tags"]
        assert "new-tag" in product["tags"]
        # No duplicates
        assert product["tags"].count("existing-tag") == 1

    def test_appends_source(self, merger: TieredMerger, tmp_path: Any) -> None:
        filepath = tmp_path / "test-product.json"
        filepath.write_text(json.dumps(_valid_product_json()), encoding="utf-8")

        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.merge_update(
                "test-product",
                _make_product(source_url="https://new-source.com"),
            )

        urls = [s["url"] for s in product["sources"]]
        assert "https://new-source.com" in urls


class TestTierRules:
    def test_t1_overwrites_t2(self, merger: TieredMerger) -> None:
        assert merger._should_overwrite(existing_tier=2, new_tier=1) is True

    def test_t2_does_not_overwrite_t1(self, merger: TieredMerger) -> None:
        assert merger._should_overwrite(existing_tier=1, new_tier=2) is False

    def test_same_tier_no_overwrite(self, merger: TieredMerger) -> None:
        assert merger._should_overwrite(existing_tier=2, new_tier=2) is False

    def test_empty_field_always_fills(self, merger: TieredMerger) -> None:
        assert merger._should_overwrite(existing_tier=None, new_tier=4) is True

    def test_t4_restricted_to_hiring(self, merger: TieredMerger) -> None:
        assert (
            merger._is_allowed_field("hiring.is_hiring", SourceTier.T4_AUXILIARY)
            is True
        )
        assert merger._is_allowed_field("description", SourceTier.T4_AUXILIARY) is False
        assert (
            merger._is_allowed_field("company.name", SourceTier.T4_AUXILIARY) is False
        )

    def test_non_t4_can_write_anything(self, merger: TieredMerger) -> None:
        assert (
            merger._is_allowed_field("description", SourceTier.T1_AUTHORITATIVE) is True
        )
        assert merger._is_allowed_field("description", SourceTier.T2_OPEN_WEB) is True
        assert (
            merger._is_allowed_field("hiring.is_hiring", SourceTier.T2_OPEN_WEB) is True
        )


class TestMergeOrCreate:
    def test_creates_when_not_exists(self, merger: TieredMerger, tmp_path: Any) -> None:
        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.merge_or_create("new-product", _make_product())

        assert product["slug"] == "new-product"
        assert (tmp_path / "new-product.json").exists()

    def test_merges_when_exists(self, merger: TieredMerger, tmp_path: Any) -> None:
        filepath = tmp_path / "existing.json"
        filepath.write_text(
            json.dumps(_valid_product_json("existing")), encoding="utf-8"
        )

        with patch("scrapers.enrichment.merger.PRODUCTS_DIR", tmp_path):
            product = merger.merge_or_create(
                "existing",
                _make_product(company_founded_year=2020),
            )

        assert product["company"]["founded_year"] == 2020


class TestBuildCompanyUrl:
    def test_prefers_website(self) -> None:
        sp = _make_product(company_website="https://company.com")
        assert TieredMerger._build_company_url(sp) == "https://company.com"

    def test_falls_back_to_wikipedia(self) -> None:
        sp = _make_product(
            company_website=None,
            company_wikipedia_url="https://en.wikipedia.org/wiki/TestCo",
        )
        assert "wikipedia.org" in TieredMerger._build_company_url(sp)

    def test_falls_back_to_bing_search(self) -> None:
        sp = _make_product(company_website=None, company_wikipedia_url=None)
        url = TieredMerger._build_company_url(sp)
        assert "bing.com/search" in url
        assert "TestCo" in url
