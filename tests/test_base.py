"""Tests for base module: SourceTier, ScrapedProduct, BaseScraper."""

from __future__ import annotations

import pytest

from scrapers.base import (
    BaseScraper,
    DiscoveredName,
    ScrapedCompany,
    ScrapedProduct,
    SourceTier,
)


class TestSourceTier:
    def test_tier_values(self) -> None:
        assert SourceTier.T1_AUTHORITATIVE == 1
        assert SourceTier.T2_OPEN_WEB == 2
        assert SourceTier.T3_AI_GENERATED == 3
        assert SourceTier.T4_AUXILIARY == 4

    def test_trust_scores(self) -> None:
        assert SourceTier.T1_AUTHORITATIVE.trust_score == 0.95
        assert SourceTier.T2_OPEN_WEB.trust_score == 0.75
        assert SourceTier.T3_AI_GENERATED.trust_score == 0.50
        assert SourceTier.T4_AUXILIARY.trust_score == 0.20

    def test_ordering(self) -> None:
        assert SourceTier.T1_AUTHORITATIVE < SourceTier.T2_OPEN_WEB
        assert SourceTier.T2_OPEN_WEB < SourceTier.T3_AI_GENERATED
        assert SourceTier.T3_AI_GENERATED < SourceTier.T4_AUXILIARY


class TestScrapedProduct:
    def test_minimal_creation(self) -> None:
        product = ScrapedProduct(name="TestProduct", source="test")
        assert product.name == "TestProduct"
        assert product.source == "test"
        assert product.source_tier == SourceTier.T2_OPEN_WEB

    def test_frozen(self) -> None:
        product = ScrapedProduct(name="Test", source="test")
        with pytest.raises(AttributeError):
            product.name = "Changed"  # type: ignore[misc]

    def test_default_values(self) -> None:
        product = ScrapedProduct(name="Test", source="test")
        assert product.description is None
        assert product.website is None if hasattr(product, "website") else True
        assert product.tags == ()
        assert product.keywords == ()
        assert product.key_people == ()
        assert product.extra == {}

    def test_all_fields(self) -> None:
        product = ScrapedProduct(
            name="FullProduct",
            source="test",
            source_url="https://test.com",
            source_tier=SourceTier.T1_AUTHORITATIVE,
            name_zh="完整产品",
            product_url="https://product.com",
            icon_url="https://product.com/icon.png",
            description="A full test product.",
            description_zh="完整测试产品。",
            product_type="llm",
            category="ai-model",
            sub_category="text-generation",
            tags=("ai", "nlp"),
            keywords=("ml",),
            company_name="TestCo",
            company_name_zh="测试公司",
            company_website="https://testco.com",
            company_founded_year=2020,
            company_headquarters_city="SF",
            company_headquarters_country="United States",
            company_headquarters_country_code="US",
            company_total_raised_usd=1000000.0,
            company_last_round="series-a",
            company_employee_count_range="11-50",
            architecture="transformer",
            parameter_count="70B",
            context_window=128000,
            modalities=("text", "image"),
            open_source=True,
            license="MIT",
            repository_url="https://github.com/test",
            github_stars=10000,
            api_available=True,
            pricing_model="freemium",
            has_free_tier=True,
            status="active",
            release_date="2024-01-01",
            hiring_positions=({"title": "ML Engineer", "location": "SF"},),
            hiring_tech_stack=("python", "pytorch"),
        )
        assert product.company_founded_year == 2020
        assert product.modalities == ("text", "image")
        assert len(product.hiring_positions) == 1

    def test_tuples_for_immutability(self) -> None:
        product = ScrapedProduct(
            name="Test",
            source="test",
            tags=("a", "b"),
            keywords=("c",),
        )
        assert isinstance(product.tags, tuple)
        assert isinstance(product.keywords, tuple)


class TestScrapedCompanyAlias:
    def test_alias_is_scraped_product(self) -> None:
        """ScrapedCompany is a backwards-compat alias for ScrapedProduct."""
        assert ScrapedCompany is ScrapedProduct

    def test_can_create_via_alias(self) -> None:
        company = ScrapedCompany(name="Test", source="test")
        assert isinstance(company, ScrapedProduct)


class TestDiscoveredName:
    def test_creation(self) -> None:
        dn = DiscoveredName(
            name="TestProduct",
            source="github",
            source_url="https://github.com/test",
        )
        assert dn.name == "TestProduct"
        assert dn.source == "github"
        assert dn.source_url == "https://github.com/test"

    def test_frozen(self) -> None:
        dn = DiscoveredName(name="Test", source="test")
        with pytest.raises(AttributeError):
            dn.name = "Changed"  # type: ignore[misc]

    def test_defaults(self) -> None:
        dn = DiscoveredName(name="Test", source="test")
        assert dn.source_url == ""
        assert dn.discovered_at == ""


class TestBaseScraper:
    def test_abstract_methods(self) -> None:
        """Cannot instantiate BaseScraper directly."""
        with pytest.raises(TypeError):
            BaseScraper()  # type: ignore[abstract]

    def test_concrete_implementation(self) -> None:
        class FakeScraper(BaseScraper):
            @property
            def source_name(self) -> str:
                return "fake"

            @property
            def source_tier(self) -> SourceTier:
                return SourceTier.T2_OPEN_WEB

            def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
                return []

        scraper = FakeScraper()
        assert scraper.source_name == "fake"
        assert scraper.source_tier == SourceTier.T2_OPEN_WEB
        assert scraper.scrape() == []

    def test_discover_default(self) -> None:
        class FakeScraper(BaseScraper):
            @property
            def source_name(self) -> str:
                return "fake"

            @property
            def source_tier(self) -> SourceTier:
                return SourceTier.T2_OPEN_WEB

            def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
                return []

        scraper = FakeScraper()
        assert scraper.discover() == []

    def test_repr(self) -> None:
        class FakeScraper(BaseScraper):
            @property
            def source_name(self) -> str:
                return "fake"

            @property
            def source_tier(self) -> SourceTier:
                return SourceTier.T2_OPEN_WEB

            def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
                return []

        scraper = FakeScraper()
        r = repr(scraper)
        assert "FakeScraper" in r
        assert "fake" in r
        assert "T2_OPEN_WEB" in r
