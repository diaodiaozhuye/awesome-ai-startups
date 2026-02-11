"""Validate company JSON files against the JSON Schema."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import jsonschema

from scrapers.config import COMPANIES_DIR, SCHEMA_FILE


@dataclass
class ValidationResult:
    """Result of validating a single company file."""

    filepath: Path
    valid: bool
    errors: list[str]


class SchemaValidator:
    """Validate company JSON files against company.schema.json."""

    def __init__(self) -> None:
        schema_text = SCHEMA_FILE.read_text(encoding="utf-8")
        self._schema = json.loads(schema_text)

    def validate_file(self, filepath: Path) -> ValidationResult:
        """Validate a single company JSON file."""
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

    def validate_all(self) -> list[ValidationResult]:
        """Validate all company JSON files in the data directory."""
        results: list[ValidationResult] = []

        if not COMPANIES_DIR.exists():
            return results

        for filepath in sorted(COMPANIES_DIR.glob("*.json")):
            results.append(self.validate_file(filepath))

        return results
