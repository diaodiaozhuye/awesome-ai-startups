"""Generate stats.json — aggregated statistics for the analytics page."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Any

from scrapers.config import PRODUCTS_DIR, STATS_FILE


class StatsGenerator:
    """Generate data/stats.json with aggregated statistics.

    Produces:
    - Total product count
    - Distribution by category, product type, sub-category, country, status
    - Funding leaderboard
    - Recently added products
    """

    def generate(self) -> dict[str, Any]:
        """Generate stats.json and return the data."""
        all_products: list[dict[str, Any]] = []

        for filepath in sorted(PRODUCTS_DIR.glob("*.json")):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                all_products.append(data)
            except (json.JSONDecodeError, OSError):
                continue

        stats: dict[str, Any] = {
            "generated_at": date.today().isoformat(),
            "total_products": len(all_products),
            "by_category": self._count_by_field(all_products, "category"),
            "by_product_type": self._count_by_field(all_products, "product_type"),
            "by_sub_category": self._count_by_field(all_products, "sub_category"),
            "by_country": self._count_by_country(all_products),
            "by_status": self._count_by_field(all_products, "status"),
            "funding_leaderboard": self._funding_leaderboard(all_products, top_n=10),
            "total_funding_usd": self._total_funding(all_products),
            "open_source_count": sum(1 for p in all_products if p.get("open_source")),
            "recently_added": self._recently_added(all_products, top_n=5),
        }

        STATS_FILE.write_text(
            json.dumps(stats, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        return stats

    @staticmethod
    def _count_by_field(
        products: list[dict[str, Any]], field: str
    ) -> list[dict[str, Any]]:
        counter: Counter[str] = Counter()
        for p in products:
            value = p.get(field)
            if value is not None:
                counter[str(value)] += 1
        return [{"label": k, "count": v} for k, v in counter.most_common()]

    @staticmethod
    def _count_by_country(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counter: Counter[str] = Counter()
        for p in products:
            country = p.get("company", {}).get("headquarters", {}).get("country")
            if country:
                counter[country] += 1
        return [{"label": k, "count": v} for k, v in counter.most_common()]

    @staticmethod
    def _funding_leaderboard(
        products: list[dict[str, Any]], top_n: int = 10
    ) -> list[dict[str, Any]]:
        funded: list[dict[str, Any]] = []
        for p in products:
            total = p.get("company", {}).get("funding", {}).get("total_raised_usd", 0)
            if total and total > 0:
                funded.append(
                    {
                        "slug": p["slug"],
                        "name": p["name"],
                        "total_raised_usd": total,
                        "valuation_usd": (
                            p.get("company", {})
                            .get("funding", {})
                            .get("valuation_usd", 0)
                        ),
                    }
                )
        funded.sort(key=lambda x: -x["total_raised_usd"])
        return funded[:top_n]

    @staticmethod
    def _total_funding(products: list[dict[str, Any]]) -> float:
        return sum(
            p.get("company", {}).get("funding", {}).get("total_raised_usd", 0)
            for p in products
        )

    @staticmethod
    def _recently_added(
        products: list[dict[str, Any]], top_n: int = 5
    ) -> list[dict[str, str]]:
        with_dates: list[dict[str, str]] = []
        for p in products:
            added = p.get("meta", {}).get("added_date")
            if added:
                with_dates.append(
                    {"slug": p["slug"], "name": p["name"], "added_date": added}
                )
        with_dates.sort(key=lambda x: x["added_date"], reverse=True)
        return with_dates[:top_n]
