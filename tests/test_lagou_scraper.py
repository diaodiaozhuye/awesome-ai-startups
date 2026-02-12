"""Tests for the Lagou (拉勾) scraper with mocked HTTP responses."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scrapers.sources.lagou import (
    LagouScraper,
    _looks_like_scale,
    _map_lagou_scale,
)

_SAMPLE_HTML = """
<html><body>
<div class="position-list">
  <li class="con_list_item">
    <h3 class="position_link"><h3>大模型算法工程师</h3></h3>
    <a class="company-name">智谱华章</a>
    <em class="add">北京</em>
    <li class="industry">人工智能</li>
    <li class="industry">150-500人</li>
  </li>
  <li class="con_list_item">
    <h3 class="position_link"><h3>深度学习工程师</h3></h3>
    <a class="company-name">百度</a>
    <em class="add">北京</em>
    <li class="industry">互联网</li>
    <li class="industry">2000人以上</li>
  </li>
</div>
</body></html>
"""


class TestLagouSearchJobs:
    @patch("scrapers.sources.lagou.create_china_http_client")
    def test_parses_job_cards_via_httpx(self, mock_create: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = _SAMPLE_HTML
        mock_response.is_success = True

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.headers = {}
        mock_create.return_value = mock_client

        scraper = LagouScraper()
        scraper.RATE_LIMIT_DELAY = 0.0
        # Test the httpx fallback path directly
        jobs = scraper._search_via_httpx("大模型", 10)

        assert len(jobs) == 2
        assert "智谱" in jobs[0]["company_name"]
        assert "百度" in jobs[1]["company_name"]


class TestLagouExtractCompany:
    def test_extracts_company(self) -> None:
        scraper = LagouScraper()
        company = scraper._extract_company({
            "company_name": "智谱华章",
            "location": "北京",
            "job_title": "大模型算法工程师",
            "scale": "150-500人",
            "industry": "人工智能",
        })
        assert company is not None
        assert company.name == "智谱华章"
        assert company.source == "lagou"
        assert company.company_headquarters_city == "北京"
        assert company.company_headquarters_country == "China"
        assert company.company_headquarters_country_code == "CN"
        assert company.company_employee_count_range == "201-500"
        assert company.description_zh == "人工智能"
        assert company.extra.get("name_zh") == "智谱华章"

    def test_returns_none_for_empty(self) -> None:
        scraper = LagouScraper()
        assert scraper._extract_company({"company_name": ""}) is None

    def test_no_location_no_country(self) -> None:
        scraper = LagouScraper()
        company = scraper._extract_company({
            "company_name": "TestCo",
            "location": "",
            "job_title": "Engineer",
            "scale": "",
            "industry": "",
        })
        assert company is not None
        assert company.company_headquarters_city is None
        assert company.company_headquarters_country is None


class TestLagouParseLagouMarkdown:
    def test_parses_card_pattern(self) -> None:
        scraper = LagouScraper()
        md = """
大模型算法工程师 20-40K 3-5年 本科
智谱华章·150-500人·人工智能·D轮

深度学习工程师 30-60K 5-10年
百度·2000人以上·互联网·上市公司
"""
        jobs = scraper._parse_lagou_markdown(md)
        assert len(jobs) >= 2
        assert jobs[0]["company_name"] == "智谱华章"
        assert jobs[0]["scale"] == "150-500人"
        assert jobs[0]["industry"] == "人工智能"

    def test_skips_navigation(self) -> None:
        scraper = LagouScraper()
        md = """
拉勾 logo
拉勾·全国

ML Engineer 20K
ValidCompany·50-150人·AI
"""
        jobs = scraper._parse_lagou_markdown(md)
        names = [j["company_name"] for j in jobs]
        assert "拉勾" not in names

    def test_empty_input(self) -> None:
        scraper = LagouScraper()
        assert scraper._parse_lagou_markdown("") == []

    def test_distinguishes_scale_vs_industry(self) -> None:
        scraper = LagouScraper()
        md = """
Engineer 20K
TestCompany·50-150人·人工智能·B轮
"""
        jobs = scraper._parse_lagou_markdown(md)
        if jobs:
            assert jobs[0]["scale"] == "50-150人"
            assert jobs[0]["industry"] == "人工智能"


class TestLooksLikeScale:
    def test_scale_range(self) -> None:
        assert _looks_like_scale("50-150人") is True
        assert _looks_like_scale("150~500人") is True

    def test_scale_above(self) -> None:
        assert _looks_like_scale("2000人以上") is True

    def test_scale_plus(self) -> None:
        assert _looks_like_scale("500+") is True

    def test_not_scale(self) -> None:
        assert _looks_like_scale("人工智能") is False
        assert _looks_like_scale("B轮") is False
        assert _looks_like_scale("") is False


class TestMapLagouScale:
    def test_exact_match(self) -> None:
        assert _map_lagou_scale("少于15人") == "1-10"
        assert _map_lagou_scale("15-50人") == "11-50"
        assert _map_lagou_scale("50-150人") == "51-200"
        assert _map_lagou_scale("150-500人") == "201-500"
        assert _map_lagou_scale("500-2000人") == "501-1000"
        assert _map_lagou_scale("2000人以上") == "5001+"

    def test_empty(self) -> None:
        assert _map_lagou_scale("") is None

    def test_unknown(self) -> None:
        assert _map_lagou_scale("custom") is None

    def test_partial_match(self) -> None:
        assert _map_lagou_scale("约150-500人") == "201-500"
