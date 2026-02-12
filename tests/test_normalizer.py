"""Tests for the Normalizer."""

from __future__ import annotations

import pytest

from scrapers.base import ScrapedProduct
from scrapers.enrichment.normalizer import Normalizer


@pytest.fixture
def normalizer() -> Normalizer:
    return Normalizer()


class TestNormalizeName:
    def test_strips_inc(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(name="Acme Inc.", source="test")
        result = normalizer.normalize(product)
        assert result.name == "Acme"

    def test_strips_llc(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(name="Acme LLC", source="test")
        result = normalizer.normalize(product)
        assert result.name == "Acme"

    def test_strips_ltd(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(name="Acme Ltd", source="test")
        result = normalizer.normalize(product)
        assert result.name == "Acme"

    def test_preserves_normal_name(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(name="OpenAI", source="test")
        result = normalizer.normalize(product)
        assert result.name == "OpenAI"


class TestNormalizeCountry:
    def test_normalizes_us(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(
            name="Test", source="test", company_headquarters_country="us"
        )
        result = normalizer.normalize(product)
        assert result.company_headquarters_country == "United States"
        assert result.company_headquarters_country_code == "US"

    def test_normalizes_uk(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(
            name="Test", source="test", company_headquarters_country="UK"
        )
        result = normalizer.normalize(product)
        assert result.company_headquarters_country == "United Kingdom"
        assert result.company_headquarters_country_code == "GB"

    def test_preserves_unknown_country(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(
            name="Test", source="test", company_headquarters_country="Atlantis"
        )
        result = normalizer.normalize(product)
        assert result.company_headquarters_country == "Atlantis"


class TestNormalizeUrl:
    def test_strips_trailing_slash(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(
            name="Test", source="test", company_website="https://example.com/"
        )
        result = normalizer.normalize(product)
        assert result.company_website == "https://example.com"

    def test_strips_fragment(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(
            name="Test", source="test", company_website="https://example.com#about"
        )
        result = normalizer.normalize(product)
        assert result.company_website == "https://example.com"


class TestQualityScore:
    def test_full_data(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(
            name="Test",
            source="test",
            company_website="https://test.com",
            description="desc",
            category="ai-other",
            company_founded_year=2023,
            company_headquarters_country="US",
            company_total_raised_usd=100000,
            company_employee_count_range="11-50",
        )
        score = normalizer.compute_quality_score(product)
        assert score == 1.0

    def test_minimal_data(self, normalizer: Normalizer) -> None:
        product = ScrapedProduct(name="Test", source="test")
        score = normalizer.compute_quality_score(product)
        assert score < 0.5
