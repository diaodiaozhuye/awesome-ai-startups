"""Tests for the ProductSchemaValidator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scrapers.validation.schema_validator import ProductSchemaValidator


@pytest.fixture
def validator() -> ProductSchemaValidator:
    return ProductSchemaValidator()


def _valid_product_data(slug: str = "test-product") -> dict:
    """Return a minimal valid product dict matching product.schema.json."""
    return {
        "slug": slug,
        "name": "Test Product",
        "product_url": "https://test-product.com",
        "description": "A valid test product with a proper description for testing.",
        "product_type": "app",
        "category": "ai-application",
        "status": "active",
        "company": {
            "name": "Test Co",
            "url": "https://test.co",
        },
    }


class TestValidateFile:
    def test_valid_product(
        self, validator: ProductSchemaValidator, tmp_path: Path
    ) -> None:
        data = _valid_product_data()
        filepath = tmp_path / "test-product.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate_file(filepath)
        assert result.valid, f"Errors: {result.errors}"

    def test_missing_required_field(
        self, validator: ProductSchemaValidator, tmp_path: Path
    ) -> None:
        data = {
            "slug": "test-product",
            "name": "Test Product",
            # missing product_url, description, product_type, category, status
        }
        filepath = tmp_path / "test-product.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate_file(filepath)
        assert not result.valid
        assert any("required" in e.lower() for e in result.errors)

    def test_slug_mismatch(
        self, validator: ProductSchemaValidator, tmp_path: Path
    ) -> None:
        data = _valid_product_data("wrong-slug")
        filepath = tmp_path / "test-product.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate_file(filepath)
        assert not result.valid
        assert any("slug mismatch" in e.lower() for e in result.errors)

    def test_invalid_category(
        self, validator: ProductSchemaValidator, tmp_path: Path
    ) -> None:
        data = _valid_product_data()
        data["category"] = "not-a-real-category"
        filepath = tmp_path / "test-product.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate_file(filepath)
        assert not result.valid

    def test_invalid_product_type(
        self, validator: ProductSchemaValidator, tmp_path: Path
    ) -> None:
        data = _valid_product_data()
        data["product_type"] = "invalid-type"
        filepath = tmp_path / "test-product.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate_file(filepath)
        assert not result.valid

    def test_invalid_json(
        self, validator: ProductSchemaValidator, tmp_path: Path
    ) -> None:
        filepath = tmp_path / "broken.json"
        filepath.write_text("{invalid json", encoding="utf-8")

        result = validator.validate_file(filepath)
        assert not result.valid
        assert any("invalid json" in e.lower() for e in result.errors)


class TestValidateProductDict:
    def test_valid_dict(self, validator: ProductSchemaValidator) -> None:
        data = _valid_product_data()
        result = validator.validate_product_dict(data, "test-product")
        assert result.valid, f"Errors: {result.errors}"

    def test_slug_mismatch_in_dict(self, validator: ProductSchemaValidator) -> None:
        data = _valid_product_data("wrong-slug")
        result = validator.validate_product_dict(data, "test-product")
        assert not result.valid
        assert any("slug mismatch" in e.lower() for e in result.errors)


class TestValidateAllSeedData:
    def test_validate_all_seed_data(self, validator: ProductSchemaValidator) -> None:
        """Integration test: all seed products should be valid."""
        results = validator.validate_all()
        assert len(results) >= 28

        for r in results:
            assert r.valid, f"{r.filepath.name}: {r.errors}"
