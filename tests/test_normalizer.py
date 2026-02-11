"""Tests for the Normalizer."""

from __future__ import annotations

import pytest

from scrapers.base import ScrapedCompany
from scrapers.enrichment.normalizer import Normalizer


@pytest.fixture
def normalizer() -> Normalizer:
    return Normalizer()


class TestNormalizeName:
    def test_strips_inc(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(name="Acme Inc.", source="test")
        result = normalizer.normalize(company)
        assert result.name == "Acme"

    def test_strips_llc(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(name="Acme LLC", source="test")
        result = normalizer.normalize(company)
        assert result.name == "Acme"

    def test_strips_ltd(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(name="Acme Ltd", source="test")
        result = normalizer.normalize(company)
        assert result.name == "Acme"

    def test_preserves_normal_name(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(name="OpenAI", source="test")
        result = normalizer.normalize(company)
        assert result.name == "OpenAI"


class TestNormalizeCountry:
    def test_normalizes_us(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(name="Test", source="test", headquarters_country="us")
        result = normalizer.normalize(company)
        assert result.headquarters_country == "United States"
        assert result.headquarters_country_code == "US"

    def test_normalizes_uk(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(name="Test", source="test", headquarters_country="UK")
        result = normalizer.normalize(company)
        assert result.headquarters_country == "United Kingdom"
        assert result.headquarters_country_code == "GB"

    def test_preserves_unknown_country(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(
            name="Test", source="test", headquarters_country="Atlantis"
        )
        result = normalizer.normalize(company)
        assert result.headquarters_country == "Atlantis"


class TestNormalizeUrl:
    def test_strips_trailing_slash(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(
            name="Test", source="test", website="https://example.com/"
        )
        result = normalizer.normalize(company)
        assert result.website == "https://example.com"

    def test_strips_fragment(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(
            name="Test", source="test", website="https://example.com#about"
        )
        result = normalizer.normalize(company)
        assert result.website == "https://example.com"


class TestQualityScore:
    def test_full_data(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(
            name="Test",
            source="test",
            website="https://test.com",
            description="desc",
            category="ai-other",
            founded_year=2023,
            headquarters_country="US",
            total_raised_usd=100000,
            employee_count_range="11-50",
        )
        score = normalizer.compute_quality_score(company)
        assert score == 1.0

    def test_minimal_data(self, normalizer: Normalizer) -> None:
        company = ScrapedCompany(name="Test", source="test")
        score = normalizer.compute_quality_score(company)
        assert score < 0.5
