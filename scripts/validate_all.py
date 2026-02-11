#!/usr/bin/env python3
"""Validate all company JSON files against the schema.

Usage:
    python scripts/validate_all.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrapers.validation.schema_validator import SchemaValidator


def main() -> None:
    validator = SchemaValidator()
    results = validator.validate_all()

    valid_count = sum(1 for r in results if r.valid)
    invalid_count = len(results) - valid_count

    for r in results:
        status = "OK" if r.valid else "FAIL"
        print(f"  {status:4s} {r.filepath.name}")
        for error in r.errors:
            print(f"       - {error}")

    print(f"\n{valid_count} valid, {invalid_count} invalid out of {len(results)} files")

    if invalid_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
