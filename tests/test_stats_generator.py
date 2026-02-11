"""Tests for stats and index generators."""

from __future__ import annotations

from scrapers.generators.index_generator import IndexGenerator
from scrapers.generators.stats_generator import StatsGenerator


class TestIndexGenerator:
    def test_generates_index(self, tmp_path: object) -> None:
        """Integration test: generate index from actual seed data."""
        gen = IndexGenerator()
        companies = gen.generate()

        assert len(companies) >= 28
        assert all("slug" in c for c in companies)
        assert all("name" in c for c in companies)
        assert all("category" in c for c in companies)
        assert all("country" in c for c in companies)

    def test_index_sorted_by_funding(self) -> None:
        gen = IndexGenerator()
        companies = gen.generate()

        funding_values = [c.get("total_raised_usd", 0) for c in companies]
        assert funding_values == sorted(funding_values, reverse=True)


class TestStatsGenerator:
    def test_generates_stats(self) -> None:
        """Integration test: generate stats from actual seed data."""
        gen = StatsGenerator()
        stats = gen.generate()

        assert stats["total_companies"] >= 28
        assert stats["total_funding_usd"] > 0
        assert len(stats["by_category"]) > 0
        assert len(stats["by_country"]) > 0
        assert len(stats["funding_leaderboard"]) > 0
        assert stats["open_source_count"] > 0

    def test_funding_leaderboard_order(self) -> None:
        gen = StatsGenerator()
        stats = gen.generate()

        leaderboard = stats["funding_leaderboard"]
        funding_values = [e["total_raised_usd"] for e in leaderboard]
        assert funding_values == sorted(funding_values, reverse=True)
