"""Generate index.json — a lightweight company listing for the frontend."""

from __future__ import annotations

import json
from typing import Any

from scrapers.config import COMPANIES_DIR, INDEX_FILE


class IndexGenerator:
    """Generate data/index.json from individual company files.

    index.json contains a lightweight array of companies with only the fields
    needed for the list page, avoiding the need to load each file individually.
    """

    # Fields to include in the index entry
    INDEX_FIELDS = [
        "slug",
        "name",
        "name_zh",
        "description",
        "description_zh",
        "website",
        "category",
        "tags",
        "founded_year",
        "open_source",
        "status",
    ]

    def generate(self) -> list[dict[str, Any]]:
        """Generate index.json and return the data."""
        companies: list[dict[str, Any]] = []

        for filepath in sorted(COMPANIES_DIR.glob("*.json")):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            entry: dict[str, Any] = {}
            for field in self.INDEX_FIELDS:
                if field in data:
                    entry[field] = data[field]

            # Extract nested fields into flat index fields
            hq = data.get("headquarters", {})
            entry["country"] = hq.get("country", "")
            entry["country_code"] = hq.get("country_code", "")
            entry["city"] = hq.get("city", "")

            funding = data.get("funding", {})
            entry["total_raised_usd"] = funding.get("total_raised_usd", 0)
            entry["last_round"] = funding.get("last_round", "")
            entry["valuation_usd"] = funding.get("valuation_usd", 0)

            team = data.get("team", {})
            entry["employee_count_range"] = team.get("employee_count_range", "")

            companies.append(entry)

        # Sort by total funding descending, then name
        companies.sort(key=lambda c: (-c.get("total_raised_usd", 0), c.get("name", "")))

        output = {
            "total": len(companies),
            "companies": companies,
        }

        INDEX_FILE.write_text(
            json.dumps(output, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        return companies
