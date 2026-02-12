"""Tests for the Deduplicator."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scrapers.base import ScrapedProduct
from scrapers.enrichment.deduplicator import Deduplicator

_FIXTURE_DATA: dict[str, dict] = {
    "openai": {
        "slug": "openai",
        "name": "ChatGPT",
        "product_url": "https://chat.openai.com",
        "company": {
            "name": "OpenAI",
            "url": "https://openai.com",
            "website": "https://openai.com",
        },
    },
    "anthropic": {
        "slug": "anthropic",
        "name": "Claude",
        "product_url": "https://claude.ai",
        "company": {
            "name": "Anthropic",
            "url": "https://www.anthropic.com",
            "website": "https://www.anthropic.com",
        },
    },
}


def _create_mock_products_dir(tmp_path: Path) -> Path:
    """Create a temporary products dir with known entries."""
    products_dir = tmp_path / "products"
    products_dir.mkdir()

    for slug, data in _FIXTURE_DATA.items():
        (products_dir / f"{slug}.json").write_text(json.dumps(data), encoding="utf-8")

    return products_dir


class TestDeduplicator:
    def test_detects_existing_by_domain(self, tmp_path: Path) -> None:
        products_dir = _create_mock_products_dir(tmp_path)
        with patch("scrapers.enrichment.deduplicator.PRODUCTS_DIR", products_dir):
            dedup = Deduplicator()
            products = [
                ScrapedProduct(
                    name="OpenAI Inc",
                    source="test",
                    company_website="https://openai.com/about",
                ),
            ]
            result = dedup.deduplicate(products)
            assert len(result.new_products) == 0
            assert len(result.updates_for_existing) == 1
            assert result.updates_for_existing[0][0] == "openai"

    def test_detects_existing_by_name(self, tmp_path: Path) -> None:
        products_dir = _create_mock_products_dir(tmp_path)
        with patch("scrapers.enrichment.deduplicator.PRODUCTS_DIR", products_dir):
            dedup = Deduplicator()
            products = [
                ScrapedProduct(name="Claude", source="test"),
            ]
            result = dedup.deduplicate(products)
            assert len(result.new_products) == 0
            assert len(result.updates_for_existing) == 1

    def test_identifies_new_product(self, tmp_path: Path) -> None:
        products_dir = _create_mock_products_dir(tmp_path)
        with patch("scrapers.enrichment.deduplicator.PRODUCTS_DIR", products_dir):
            dedup = Deduplicator()
            products = [
                ScrapedProduct(
                    name="Brand New Startup",
                    source="test",
                    product_url="https://newstartup.ai",
                ),
            ]
            result = dedup.deduplicate(products)
            assert len(result.new_products) == 1
            assert len(result.updates_for_existing) == 0

    def test_mixed_new_and_existing(self, tmp_path: Path) -> None:
        products_dir = _create_mock_products_dir(tmp_path)
        with patch("scrapers.enrichment.deduplicator.PRODUCTS_DIR", products_dir):
            dedup = Deduplicator()
            products = [
                ScrapedProduct(
                    name="ChatGPT",
                    source="test",
                    product_url="https://chat.openai.com",
                ),
                ScrapedProduct(
                    name="New AI Corp",
                    source="test",
                    product_url="https://newai.com",
                ),
            ]
            result = dedup.deduplicate(products)
            assert len(result.new_products) == 1
            assert len(result.updates_for_existing) == 1
