"""Validate product JSON files against the JSON Schema."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import jsonschema

from scrapers.config import PRODUCT_SCHEMA_FILE, PRODUCTS_DIR


@dataclass
class ValidationResult:
    """Result of validating a single product file."""

    filepath: Path
    valid: bool
    errors: list[str]


class ProductSchemaValidator:
    """Validate product JSON files against product.schema.json."""

    def __init__(self) -> None:
        schema_text = PRODUCT_SCHEMA_FILE.read_text(encoding="utf-8")
        self._schema = json.loads(schema_text)

    def validate_file(self, filepath: Path) -> ValidationResult:
        """Validate a single product JSON file."""
        errors: list[str] = []

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return ValidationResult(
                filepath=filepath, valid=False, errors=[f"Invalid JSON: {e}"]
            )

        # Check slug matches filename
        expected_slug = filepath.stem
        actual_slug = data.get("slug", "")
        if actual_slug != expected_slug:
            errors.append(
                f"Slug mismatch: file is '{expected_slug}' but slug is '{actual_slug}'"
            )

        # JSON Schema validation
        validator = jsonschema.Draft7Validator(self._schema)
        for error in validator.iter_errors(data):
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            errors.append(f"{path}: {error.message}")

        return ValidationResult(
            filepath=filepath, valid=len(errors) == 0, errors=errors
        )

    def validate_product_dict(self, data: dict, slug: str) -> ValidationResult:
        """Validate a product dict directly without reading from file.

        Useful for pipeline validation before writing to disk.
        """
        errors: list[str] = []

        # Check slug matches expected value
        actual_slug = data.get("slug", "")
        if actual_slug != slug:
            errors.append(f"Slug mismatch: expected '{slug}' but got '{actual_slug}'")

        # JSON Schema validation
        validator = jsonschema.Draft7Validator(self._schema)
        for error in validator.iter_errors(data):
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            errors.append(f"{path}: {error.message}")

        # Use a synthetic filepath based on PRODUCTS_DIR for the result
        filepath = PRODUCTS_DIR / f"{slug}.json"

        return ValidationResult(
            filepath=filepath, valid=len(errors) == 0, errors=errors
        )

    def validate_all(self) -> list[ValidationResult]:
        """Validate all product JSON files in the data directory."""
        results: list[ValidationResult] = []

        if not PRODUCTS_DIR.exists():
            return results

        for filepath in sorted(PRODUCTS_DIR.glob("*.json")):
            results.append(self.validate_file(filepath))

        return results
