"""Tests for the QualityScorer."""

from __future__ import annotations

import pytest

from scrapers.enrichment.quality_scorer import QualityScorer


@pytest.fixture
def scorer() -> QualityScorer:
    return QualityScorer()


class TestQualityScorer:
    def test_full_product_high_score(self, scorer: QualityScorer) -> None:
        product = {
            "name": "TestProduct",
            "product_url": "https://test.com",
            "description": "A comprehensive test product.",
            "product_type": "llm",
            "category": "ai-model",
            "sub_category": "text-generation",
            "icon_url": "https://test.com/icon.png",
            "company": {
                "name": "TestCo",
                "url": "https://testco.com",
                "website": "https://testco.com",
                "founded_year": 2020,
                "headquarters": {"city": "SF", "country": "US"},
                "description": "A test company.",
                "funding": {"total_raised_usd": 1000000},
            },
            "architecture": "transformer",
            "modalities": ["text"],
            "platforms": ["web", "api"],
            "api_available": True,
            "open_source": True,
            "repository_url": "https://github.com/test",
            "pricing": {"model": "freemium"},
            "tags": ["ai", "nlp"],
            "keywords": ["machine-learning"],
            "key_people": [{"name": "John", "title": "CEO"}],
            "sources": [{"url": "https://test.com", "source_name": "test"}],
            "status": "active",
            "description_zh": "测试产品",
        }
        score = scorer.score(product)
        assert score >= 0.9

    def test_minimal_product_low_score(self, scorer: QualityScorer) -> None:
        product = {
            "slug": "minimal",
            "name": "Minimal",
            "product_url": "https://minimal.com",
            "description": "A minimal product.",
            "product_type": "app",
            "category": "ai-app",
            "status": "active",
        }
        score = scorer.score(product)
        assert score < 0.5

    def test_empty_product(self, scorer: QualityScorer) -> None:
        score = scorer.score({})
        assert score == 0.0

    def test_score_between_0_and_1(self, scorer: QualityScorer) -> None:
        product = {
            "name": "Test",
            "description": "Test product",
            "company": {"name": "Co", "url": "https://co.com"},
            "tags": ["ai"],
        }
        score = scorer.score(product)
        assert 0.0 <= score <= 1.0

    def test_empty_strings_not_counted(self, scorer: QualityScorer) -> None:
        product_with_empty = {
            "name": "Test",
            "description": "",  # empty string
            "product_url": "   ",  # whitespace only
        }
        product_without = {
            "name": "Test",
        }
        # Empty string fields should not add to score
        score_with = scorer.score(product_with_empty)
        score_without = scorer.score(product_without)
        assert score_with == score_without

    def test_empty_lists_not_counted(self, scorer: QualityScorer) -> None:
        product = {
            "name": "Test",
            "tags": [],
            "keywords": [],
        }
        score = scorer.score(product)
        # Empty lists shouldn't count
        product_no_lists = {"name": "Test"}
        assert score == scorer.score(product_no_lists)

    def test_nested_field_check(self, scorer: QualityScorer) -> None:
        """Company sub-fields should be detected correctly."""
        product = {
            "company": {
                "name": "TestCo",
                "url": "https://testco.com",
                "website": "https://testco.com",
            },
        }
        score = scorer.score(product)
        # Should get credit for company.name, company.url, company.website
        assert score > 0.0
