"""Shared pytest fixtures for tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_company_data() -> dict:
    """Return a valid company data dict."""
    return {
        "slug": "test-company",
        "name": "Test Company",
        "description": "A test company for unit testing purposes with enough description length.",
        "website": "https://test-company.com",
        "category": "ai-other",
        "founded_year": 2023,
        "headquarters": {
            "city": "San Francisco",
            "country": "United States",
            "country_code": "US",
        },
        "tags": ["generative-ai"],
        "status": "active",
        "meta": {
            "added_date": "2025-01-01",
            "last_updated": "2025-01-01",
            "sources": ["https://test-company.com"],
            "data_quality_score": 0.6,
        },
    }


@pytest.fixture
def tmp_companies_dir(tmp_path: Path, sample_company_data: dict) -> Path:
    """Create a temporary companies directory with a sample file."""
    companies_dir = tmp_path / "data" / "companies"
    companies_dir.mkdir(parents=True)

    filepath = companies_dir / "test-company.json"
    filepath.write_text(json.dumps(sample_company_data, indent=2), encoding="utf-8")

    return companies_dir
