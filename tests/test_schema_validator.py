"""Tests for the SchemaValidator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scrapers.validation.schema_validator import SchemaValidator


@pytest.fixture
def validator() -> SchemaValidator:
    return SchemaValidator()


class TestSchemaValidator:
    def test_valid_company(self, validator: SchemaValidator, tmp_path: Path) -> None:
        data = {
            "slug": "test-co",
            "name": "Test Co",
            "description": "A valid test company with a proper description.",
            "website": "https://test.co",
            "category": "ai-other",
            "founded_year": 2023,
            "headquarters": {"city": "NYC", "country": "United States"},
        }
        filepath = tmp_path / "test-co.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate_file(filepath)
        assert result.valid, f"Errors: {result.errors}"

    def test_missing_required_field(
        self, validator: SchemaValidator, tmp_path: Path
    ) -> None:
        data = {
            "slug": "test-co",
            "name": "Test Co",
            # missing description, website, category, founded_year, headquarters
        }
        filepath = tmp_path / "test-co.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate_file(filepath)
        assert not result.valid
        assert any(
            "required" in e.lower() or "description" in e.lower() for e in result.errors
        )

    def test_slug_mismatch(self, validator: SchemaValidator, tmp_path: Path) -> None:
        data = {
            "slug": "wrong-slug",
            "name": "Test Co",
            "description": "A valid test company with a proper description.",
            "website": "https://test.co",
            "category": "ai-other",
            "founded_year": 2023,
            "headquarters": {"city": "NYC", "country": "United States"},
        }
        filepath = tmp_path / "test-co.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate_file(filepath)
        assert not result.valid
        assert any("slug mismatch" in e.lower() for e in result.errors)

    def test_invalid_category(self, validator: SchemaValidator, tmp_path: Path) -> None:
        data = {
            "slug": "test-co",
            "name": "Test Co",
            "description": "A valid test company with a proper description.",
            "website": "https://test.co",
            "category": "not-a-real-category",
            "founded_year": 2023,
            "headquarters": {"city": "NYC", "country": "United States"},
        }
        filepath = tmp_path / "test-co.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate_file(filepath)
        assert not result.valid

    def test_invalid_json(self, validator: SchemaValidator, tmp_path: Path) -> None:
        filepath = tmp_path / "broken.json"
        filepath.write_text("{invalid json", encoding="utf-8")

        result = validator.validate_file(filepath)
        assert not result.valid
        assert any("invalid json" in e.lower() for e in result.errors)

    def test_validate_all_seed_data(self, validator: SchemaValidator) -> None:
        """Integration test: all 28 seed companies should be valid."""
        results = validator.validate_all()
        assert len(results) >= 28

        for r in results:
            assert r.valid, f"{r.filepath.name}: {r.errors}"
