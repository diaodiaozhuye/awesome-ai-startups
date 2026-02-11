"""Generate stats.json — aggregated statistics for the analytics page."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Any

from scrapers.config import COMPANIES_DIR, STATS_FILE


class StatsGenerator:
    """Generate data/stats.json with aggregated statistics.

    Produces:
    - Total company count
    - Distribution by category, country, founded year
    - Funding leaderboard
    - Recently added companies
    """

    def generate(self) -> dict[str, Any]:
        """Generate stats.json and return the data."""
        all_companies: list[dict[str, Any]] = []

        for filepath in sorted(COMPANIES_DIR.glob("*.json")):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                all_companies.append(data)
            except (json.JSONDecodeError, OSError):
                continue

        stats: dict[str, Any] = {
            "generated_at": date.today().isoformat(),
            "total_companies": len(all_companies),
            "by_category": self._count_by_field(all_companies, "category"),
            "by_country": self._count_by_country(all_companies),
            "by_founded_year": self._count_by_field(all_companies, "founded_year"),
            "by_status": self._count_by_field(all_companies, "status"),
            "funding_leaderboard": self._funding_leaderboard(all_companies, top_n=10),
            "total_funding_usd": self._total_funding(all_companies),
            "open_source_count": sum(1 for c in all_companies if c.get("open_source")),
            "recently_added": self._recently_added(all_companies, top_n=5),
        }

        STATS_FILE.write_text(
            json.dumps(stats, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        return stats

    @staticmethod
    def _count_by_field(companies: list[dict], field: str) -> list[dict[str, Any]]:
        counter: Counter[str] = Counter()
        for c in companies:
            value = c.get(field)
            if value is not None:
                counter[str(value)] += 1
        return [{"label": k, "count": v} for k, v in counter.most_common()]

    @staticmethod
    def _count_by_country(companies: list[dict]) -> list[dict[str, Any]]:
        counter: Counter[str] = Counter()
        for c in companies:
            country = c.get("headquarters", {}).get("country")
            if country:
                counter[country] += 1
        return [{"label": k, "count": v} for k, v in counter.most_common()]

    @staticmethod
    def _funding_leaderboard(
        companies: list[dict], top_n: int = 10
    ) -> list[dict[str, Any]]:
        funded = []
        for c in companies:
            total = c.get("funding", {}).get("total_raised_usd", 0)
            if total and total > 0:
                funded.append(
                    {
                        "slug": c["slug"],
                        "name": c["name"],
                        "total_raised_usd": total,
                        "valuation_usd": c.get("funding", {}).get("valuation_usd", 0),
                    }
                )
        funded.sort(key=lambda x: -x["total_raised_usd"])
        return funded[:top_n]

    @staticmethod
    def _total_funding(companies: list[dict]) -> float:
        return sum(c.get("funding", {}).get("total_raised_usd", 0) for c in companies)

    @staticmethod
    def _recently_added(companies: list[dict], top_n: int = 5) -> list[dict[str, str]]:
        with_dates = []
        for c in companies:
            added = c.get("meta", {}).get("added_date")
            if added:
                with_dates.append(
                    {"slug": c["slug"], "name": c["name"], "added_date": added}
                )
        with_dates.sort(key=lambda x: x["added_date"], reverse=True)
        return with_dates[:top_n]
