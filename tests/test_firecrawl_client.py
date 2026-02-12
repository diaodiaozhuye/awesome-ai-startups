"""Tests for the FirecrawlClient with mocked HTTP responses."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scrapers.utils.firecrawl_client import (
    FirecrawlClient,
    FirecrawlResult,
    FirecrawlUsage,
)


class TestFirecrawlUsage:
    def test_new_usage_can_fetch(self) -> None:
        usage = FirecrawlUsage()
        assert usage.can_fetch() is True

    def test_remaining_full_quota(self) -> None:
        usage = FirecrawlUsage()
        assert usage.remaining == 100  # MAX_DAILY_FIRECRAWL_PAGES

    def test_record_fetch_increments(self) -> None:
        usage = FirecrawlUsage()
        initial = usage.remaining
        usage.record_fetch()
        assert usage.remaining == initial - 1
        assert usage.pages_used == 1

    def test_quota_exhausted(self) -> None:
        usage = FirecrawlUsage()
        for _ in range(100):
            usage.record_fetch()
        assert usage.can_fetch() is False
        assert usage.remaining == 0


class TestFirecrawlResult:
    def test_success_result(self) -> None:
        result = FirecrawlResult(
            url="https://example.com",
            markdown="# Hello",
            success=True,
        )
        assert result.success is True
        assert result.markdown == "# Hello"
        assert result.error is None

    def test_failure_result(self) -> None:
        result = FirecrawlResult(
            url="https://example.com",
            success=False,
            error="API key missing",
        )
        assert result.success is False
        assert result.error == "API key missing"

    def test_default_values(self) -> None:
        result = FirecrawlResult(url="https://example.com")
        assert result.markdown == ""
        assert result.html == ""
        assert result.metadata == {}
        assert result.success is True


class TestFirecrawlClient:
    @patch.dict("os.environ", {"FIRECRAWL_API_KEY": ""}, clear=False)
    def test_no_api_key_returns_error(self) -> None:
        with patch(
            "scrapers.utils.firecrawl_client._USAGE_FILE",
            MagicMock(exists=MagicMock(return_value=False)),
        ):
            client = FirecrawlClient()
            result = client.scrape_url("https://example.com")
            assert result.success is False
            assert "API_KEY" in result.error
            client.close()

    @patch.dict("os.environ", {"FIRECRAWL_API_KEY": "test-key"}, clear=False)
    def test_successful_scrape(self) -> None:
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "data": {
                "markdown": "# Test Page\nContent here",
                "html": "<h1>Test Page</h1>",
                "metadata": {"title": "Test"},
            }
        }

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response

        with patch(
            "scrapers.utils.firecrawl_client._USAGE_FILE",
            MagicMock(exists=MagicMock(return_value=False)),
        ):
            client = FirecrawlClient()
            client._client = mock_client
            client._last_request_time = 0

            result = client.scrape_url("https://example.com")

        assert result.success is True
        assert result.markdown == "# Test Page\nContent here"
        assert result.metadata["title"] == "Test"

    @patch.dict("os.environ", {"FIRECRAWL_API_KEY": "test-key"}, clear=False)
    def test_quota_exhausted_returns_error(self) -> None:
        with patch(
            "scrapers.utils.firecrawl_client._USAGE_FILE",
            MagicMock(exists=MagicMock(return_value=False)),
        ):
            client = FirecrawlClient()
            # Exhaust quota
            client._usage.pages_used = 100
            from datetime import date

            client._usage.date = date.today().isoformat()

            result = client.scrape_url("https://example.com")
            assert result.success is False
            assert "quota" in result.error.lower()

    def test_remaining_quota_property(self) -> None:
        with patch(
            "scrapers.utils.firecrawl_client._USAGE_FILE",
            MagicMock(exists=MagicMock(return_value=False)),
        ):
            client = FirecrawlClient()
            assert client.remaining_quota == 100

            client._usage.record_fetch()
            assert client.remaining_quota == 99

    def test_close_cleans_up(self) -> None:
        with patch(
            "scrapers.utils.firecrawl_client._USAGE_FILE",
            MagicMock(exists=MagicMock(return_value=False)),
        ):
            client = FirecrawlClient()
            mock_http = MagicMock()
            client._client = mock_http

            client.close()
            mock_http.close.assert_called_once()
            assert client._client is None
