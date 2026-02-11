"""Tests for the Indeed scraper with mocked HTTP responses."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scrapers.sources.indeed import IndeedScraper, _parse_location

_SAMPLE_HTML = """
<html><body>
<div class="jobsearch-ResultsList">
  <div class="job_seen_beacon">
    <span data-testid="company-name">OpenAI</span>
    <div data-testid="text-location">San Francisco, CA</div>
    <h2 class="jobTitle"><a class="jcs-JobTitle">Machine Learning Engineer</a></h2>
    <div class="job-snippet">Build large language models and AI systems.</div>
  </div>
  <div class="job_seen_beacon">
    <span data-testid="company-name">Anthropic</span>
    <div data-testid="text-location">San Francisco, CA</div>
    <h2 class="jobTitle"><a class="jcs-JobTitle">AI Researcher</a></h2>
    <div class="job-snippet">Research AI safety and alignment.</div>
  </div>
  <div class="job_seen_beacon">
    <span data-testid="company-name"></span>
    <div data-testid="text-location">Remote</div>
  </div>
</div>
</body></html>
"""


class TestIndeedSearchJobs:
    @patch("scrapers.sources.indeed.create_http_client")
    def test_parses_job_cards(self, mock_create: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = _SAMPLE_HTML
        mock_response.is_success = True
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_create.return_value = mock_client

        scraper = IndeedScraper()
        scraper.RATE_LIMIT_DELAY = 0.0
        jobs = scraper._search_jobs("ML Engineer", 10)

        assert len(jobs) == 2
        assert jobs[0]["company_name"] == "OpenAI"
        assert jobs[1]["company_name"] == "Anthropic"

    @patch("scrapers.sources.indeed.create_http_client")
    def test_skips_empty_company_names(self, mock_create: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = _SAMPLE_HTML
        mock_response.is_success = True
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_create.return_value = mock_client

        scraper = IndeedScraper()
        scraper.RATE_LIMIT_DELAY = 0.0
        jobs = scraper._search_jobs("ML Engineer", 10)
        # The third card has empty company name, should be skipped
        assert all(j["company_name"] for j in jobs)


class TestIndeedExtractCompany:
    def test_extracts_company(self) -> None:
        scraper = IndeedScraper()
        company = scraper._extract_company(
            {
                "company_name": "OpenAI",
                "location": "San Francisco, CA",
                "job_title": "LLM Engineer",
                "snippet": "Build large language models.",
            }
        )
        assert company is not None
        assert company.name == "OpenAI"
        assert company.source == "indeed"
        assert company.headquarters_city == "San Francisco"
        assert company.headquarters_country == "United States"
        assert company.category == "llm-foundation-model"

    def test_returns_none_for_empty_name(self) -> None:
        scraper = IndeedScraper()
        company = scraper._extract_company({"company_name": "", "location": ""})
        assert company is None


class TestParseLocation:
    def test_us_city_state(self) -> None:
        city, country = _parse_location("San Francisco, CA")
        assert city == "San Francisco"
        assert country == "United States"

    def test_international(self) -> None:
        city, country = _parse_location("London, United Kingdom")
        assert city == "London"
        assert country == "United Kingdom"

    def test_empty(self) -> None:
        city, country = _parse_location("")
        assert city == ""
        assert country == ""

    def test_city_only(self) -> None:
        city, country = _parse_location("Remote")
        assert city == "Remote"
        assert country == ""
