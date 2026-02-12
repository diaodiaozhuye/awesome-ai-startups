"""Shared pytest fixtures for tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_product_data() -> dict:
    """Return a valid product data dict matching product.schema.json."""
    return {
        "slug": "test-product",
        "name": "Test Product",
        "product_url": "https://test-product.com",
        "description": "A test product for unit testing purposes with enough description length.",
        "product_type": "app",
        "category": "ai-app",
        "status": "active",
        "company": {
            "name": "Test Company",
            "url": "https://test-company.com",
            "website": "https://test-company.com",
            "founded_year": 2023,
            "headquarters": {
                "city": "San Francisco",
                "country": "United States",
                "country_code": "US",
            },
        },
        "tags": ["generative-ai"],
        "meta": {
            "added_date": "2025-01-01",
            "last_updated": "2025-01-01",
            "data_quality_score": 0.6,
        },
    }


# Backwards compatibility alias
sample_company_data = sample_product_data


@pytest.fixture
def tmp_products_dir(tmp_path: Path, sample_product_data: dict) -> Path:
    """Create a temporary products directory with a sample file."""
    products_dir = tmp_path / "data" / "products"
    products_dir.mkdir(parents=True)

    filepath = products_dir / "test-product.json"
    filepath.write_text(json.dumps(sample_product_data, indent=2), encoding="utf-8")

    return products_dir
