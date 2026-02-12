"""Generate index.json — a lightweight product listing for the frontend."""

from __future__ import annotations

import json
from typing import Any

from scrapers.config import INDEX_FILE, PRODUCTS_DIR


class IndexGenerator:
    """Generate data/index.json from individual product files.

    index.json contains a lightweight array of products with only the fields
    needed for the list page, avoiding the need to load each file individually.
    """

    # Fields to include in the index entry (top-level product fields)
    INDEX_FIELDS = [
        "slug",
        "name",
        "name_zh",
        "description",
        "description_zh",
        "product_url",
        "icon_url",
        "product_type",
        "category",
        "sub_category",
        "tags",
        "keywords",
        "open_source",
        "status",
    ]

    def generate(self) -> list[dict[str, Any]]:
        """Generate index.json and return the data."""
        products: list[dict[str, Any]] = []

        for filepath in sorted(PRODUCTS_DIR.glob("*.json")):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            entry: dict[str, Any] = {}
            for field in self.INDEX_FIELDS:
                if field in data:
                    entry[field] = data[field]

            # Extract nested company fields into flat index fields
            company = data.get("company", {})
            entry["company_name"] = company.get("name", "")
            entry["company_url"] = company.get("url", "")

            hq = company.get("headquarters", {})
            entry["country"] = hq.get("country", "")
            entry["country_code"] = hq.get("country_code", "")
            entry["city"] = hq.get("city", "")

            funding = company.get("funding", {})
            entry["total_raised_usd"] = funding.get("total_raised_usd", 0)
            entry["last_round"] = funding.get("last_round", "")
            entry["valuation_usd"] = funding.get("valuation_usd", 0)

            entry["employee_count_range"] = company.get("employee_count_range", "")

            products.append(entry)

        # Sort by total funding descending, then name
        products.sort(key=lambda p: (-p.get("total_raised_usd", 0), p.get("name", "")))

        output = {
            "total": len(products),
            "products": products,
        }

        INDEX_FILE.write_text(
            json.dumps(output, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        return products
