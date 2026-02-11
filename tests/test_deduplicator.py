"""Tests for the Deduplicator."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scrapers.base import ScrapedCompany
from scrapers.enrichment.deduplicator import Deduplicator


@pytest.fixture
def mock_companies_dir(tmp_path: Path) -> Path:
    """Create a temporary companies dir with known entries."""
    companies_dir = tmp_path / "companies"
    companies_dir.mkdir()

    openai_data = {
        "slug": "openai",
        "name": "OpenAI",
        "website": "https://openai.com",
    }
    (companies_dir / "openai.json").write_text(
        json.dumps(openai_data), encoding="utf-8"
    )

    anthropic_data = {
        "slug": "anthropic",
        "name": "Anthropic",
        "website": "https://www.anthropic.com",
    }
    (companies_dir / "anthropic.json").write_text(
        json.dumps(anthropic_data), encoding="utf-8"
    )

    return companies_dir


class TestDeduplicator:
    def test_detects_existing_by_domain(self, mock_companies_dir: Path) -> None:
        with patch(
            "scrapers.enrichment.deduplicator.COMPANIES_DIR", mock_companies_dir
        ):
            dedup = Deduplicator()
            companies = [
                ScrapedCompany(
                    name="OpenAI Inc", source="test", website="https://openai.com/about"
                ),
            ]
            result = dedup.deduplicate(companies)
            assert len(result.new_companies) == 0
            assert len(result.updates_for_existing) == 1
            assert result.updates_for_existing[0][0] == "openai"

    def test_detects_existing_by_name(self, mock_companies_dir: Path) -> None:
        with patch(
            "scrapers.enrichment.deduplicator.COMPANIES_DIR", mock_companies_dir
        ):
            dedup = Deduplicator()
            companies = [
                ScrapedCompany(name="Anthropic", source="test"),
            ]
            result = dedup.deduplicate(companies)
            assert len(result.new_companies) == 0
            assert len(result.updates_for_existing) == 1

    def test_identifies_new_company(self, mock_companies_dir: Path) -> None:
        with patch(
            "scrapers.enrichment.deduplicator.COMPANIES_DIR", mock_companies_dir
        ):
            dedup = Deduplicator()
            companies = [
                ScrapedCompany(
                    name="Brand New Startup",
                    source="test",
                    website="https://newstartup.ai",
                ),
            ]
            result = dedup.deduplicate(companies)
            assert len(result.new_companies) == 1
            assert len(result.updates_for_existing) == 0

    def test_mixed_new_and_existing(self, mock_companies_dir: Path) -> None:
        with patch(
            "scrapers.enrichment.deduplicator.COMPANIES_DIR", mock_companies_dir
        ):
            dedup = Deduplicator()
            companies = [
                ScrapedCompany(
                    name="OpenAI", source="test", website="https://openai.com"
                ),
                ScrapedCompany(
                    name="New AI Corp", source="test", website="https://newai.com"
                ),
            ]
            result = dedup.deduplicate(companies)
            assert len(result.new_companies) == 1
            assert len(result.updates_for_existing) == 1
