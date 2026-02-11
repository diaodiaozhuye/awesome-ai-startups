"""Tests for BaseJobSiteScraper."""

from __future__ import annotations

from scrapers.base import ScrapedCompany
from scrapers.base_job_scraper import BaseJobSiteScraper


class _FakeJobScraper(BaseJobSiteScraper):
    """Concrete implementation for testing the base class."""

    RATE_LIMIT_DELAY = 0.0  # No delay in tests

    def __init__(self, jobs: list[list[dict[str, str]]]) -> None:
        super().__init__()
        self._jobs_by_keyword = jobs
        self._call_index = 0

    @property
    def source_name(self) -> str:
        return "fake"

    def _search_jobs(self, keyword: str, limit: int) -> list[dict[str, str]]:
        if self._call_index < len(self._jobs_by_keyword):
            result = self._jobs_by_keyword[self._call_index]
            self._call_index += 1
            return result[:limit]
        return []

    def _extract_company(self, job_data: dict[str, str]) -> ScrapedCompany | None:
        name = job_data.get("company")
        if not name:
            return None
        return ScrapedCompany(
            name=name,
            source="fake",
            website=job_data.get("website"),
            headquarters_city=job_data.get("city"),
            tags=("test",),
        )


class TestScrapeOrchestration:
    def test_returns_companies(self) -> None:
        scraper = _FakeJobScraper(
            [
                [
                    {"company": "OpenAI", "website": "https://openai.com"},
                    {"company": "Anthropic", "website": "https://anthropic.com"},
                ],
            ]
        )
        results = scraper.scrape(limit=10)
        assert len(results) == 2
        names = {c.name for c in results}
        assert names == {"OpenAI", "Anthropic"}

    def test_respects_limit(self) -> None:
        scraper = _FakeJobScraper(
            [
                [
                    {"company": f"Company{i}", "website": f"https://c{i}.com"}
                    for i in range(20)
                ],
            ]
        )
        results = scraper.scrape(limit=5)
        assert len(results) == 5

    def test_skips_none_extractions(self) -> None:
        scraper = _FakeJobScraper(
            [
                [
                    {"company": ""},  # Will produce None
                    {"company": "ValidCo", "website": "https://valid.co"},
                ],
            ]
        )
        results = scraper.scrape(limit=10)
        assert len(results) == 1
        assert results[0].name == "ValidCo"


class TestDeduplication:
    def test_deduplicates_by_domain(self) -> None:
        scraper = _FakeJobScraper(
            [
                [
                    {"company": "OpenAI", "website": "https://openai.com"},
                    {"company": "OpenAI Inc", "website": "https://openai.com"},
                ],
            ]
        )
        results = scraper.scrape(limit=10)
        assert len(results) == 1
        assert results[0].name == "OpenAI"

    def test_deduplicates_by_name(self) -> None:
        scraper = _FakeJobScraper(
            [
                [
                    {"company": "Anthropic"},
                    {"company": "anthropic"},
                ],
            ]
        )
        results = scraper.scrape(limit=10)
        assert len(results) == 1


class TestMerge:
    def test_merge_fills_missing_fields(self) -> None:
        scraper = _FakeJobScraper([[]])
        existing = ScrapedCompany(name="Test", source="fake", tags=("a",))
        incoming = ScrapedCompany(
            name="Test", source="fake", headquarters_city="SF", tags=("b",)
        )
        merged = scraper._merge(existing, incoming)
        assert merged.headquarters_city == "SF"
        assert set(merged.tags) == {"a", "b"}

    def test_merge_does_not_overwrite(self) -> None:
        scraper = _FakeJobScraper([[]])
        existing = ScrapedCompany(name="Test", source="fake", headquarters_city="NYC")
        incoming = ScrapedCompany(name="Test", source="fake", headquarters_city="SF")
        merged = scraper._merge(existing, incoming)
        assert merged.headquarters_city == "NYC"

    def test_merge_preserves_name_and_source(self) -> None:
        scraper = _FakeJobScraper([[]])
        existing = ScrapedCompany(name="Original", source="fake")
        incoming = ScrapedCompany(name="Different", source="other")
        merged = scraper._merge(existing, incoming)
        assert merged.name == "Original"
        assert merged.source == "fake"


class TestDedupKey:
    def test_domain_key(self) -> None:
        company = ScrapedCompany(
            name="Test", source="fake", website="https://www.example.com/about"
        )
        key = BaseJobSiteScraper._dedup_key(company)
        assert key == "example.com"

    def test_name_fallback(self) -> None:
        company = ScrapedCompany(name="My Company", source="fake")
        key = BaseJobSiteScraper._dedup_key(company)
        assert key == "my company"
