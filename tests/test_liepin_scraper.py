"""Tests for the Liepin (猎聘) scraper with mocked HTTP responses."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scrapers.sources.liepin import LiepinScraper, _map_liepin_scale, _normalize_city

_SAMPLE_HTML = """
<html><body>
<div class="job-list">
  <div class="job-list-item">
    <a class="company-name">北京智谱华章科技有限公司</a>
    <span class="job-dq">北京-朝阳区</span>
    <a class="job-title">大模型算法工程师</a>
    <span class="scale">1000-9999人</span>
    <span class="industry">人工智能</span>
  </div>
  <div class="job-list-item">
    <a class="company-name">深圳市腾讯计算机系统有限公司</a>
    <span class="job-dq">深圳·南山区</span>
    <a class="job-title">NLP研究员</a>
    <span class="scale">10000人以上</span>
    <span class="industry">互联网</span>
  </div>
</div>
</body></html>
"""


class TestLiepinSearchJobs:
    @patch("scrapers.sources.liepin.create_china_http_client")
    def test_parses_job_cards_via_httpx(self, mock_create: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = _SAMPLE_HTML
        mock_response.is_success = True

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.headers = {}
        mock_create.return_value = mock_client

        scraper = LiepinScraper()
        scraper.RATE_LIMIT_DELAY = 0.0
        # Test the httpx fallback path directly
        jobs = scraper._search_via_httpx("大模型", 10)

        assert len(jobs) == 2
        assert "智谱" in jobs[0]["company_name"]
        assert "腾讯" in jobs[1]["company_name"]


class TestLiepinExtractCompany:
    def test_extracts_chinese_company(self) -> None:
        scraper = LiepinScraper()
        company = scraper._extract_company({
            "company_name": "北京智谱华章科技有限公司",
            "location": "北京-朝阳区",
            "job_title": "大模型算法工程师",
            "scale": "1000-9999人",
            "industry": "人工智能",
        })
        assert company is not None
        assert company.name == "北京智谱华章科技有限公司"
        assert company.source == "liepin"
        assert company.company_headquarters_city == "北京"
        assert company.company_headquarters_country == "China"
        assert company.company_headquarters_country_code == "CN"
        assert company.company_employee_count_range == "1001-5000"
        assert company.description_zh == "人工智能"
        assert company.extra.get("name_zh") == "北京智谱华章科技有限公司"

    def test_returns_none_for_empty(self) -> None:
        scraper = LiepinScraper()
        assert scraper._extract_company({"company_name": ""}) is None

    def test_no_city_no_country(self) -> None:
        scraper = LiepinScraper()
        company = scraper._extract_company({
            "company_name": "TestCo",
            "location": "",
            "job_title": "ML Engineer",
            "scale": "",
            "industry": "",
        })
        assert company is not None
        assert company.company_headquarters_city is None
        assert company.company_headquarters_country is None


class TestLiepinParseLiepinMarkdown:
    def test_parses_liepin_card_pattern(self) -> None:
        scraper = LiepinScraper()
        md = """
[大模型算法工程师](https://www.liepin.com/job/123) 20-40K·14薪
智谱华章·北京·1000-9999人·人工智能

[NLP研究员](https://www.liepin.com/job/456) 30-50K
腾讯·深圳·10000人以上·互联网
"""
        jobs = scraper._parse_liepin_markdown(md)
        assert len(jobs) >= 2
        assert jobs[0]["company_name"] == "智谱华章"
        assert jobs[0]["job_title"] == "大模型算法工程师"

    def test_skips_navigation(self) -> None:
        scraper = LiepinScraper()
        md = """
[首页](https://www.liepin.com/) 猎聘
猎聘·全国

[ML Engineer](https://www.liepin.com/job/1) 20K
ValidCompany·北京
"""
        jobs = scraper._parse_liepin_markdown(md)
        names = [j["company_name"] for j in jobs]
        assert "猎聘" not in names
        assert "首页" not in names

    def test_empty_input(self) -> None:
        scraper = LiepinScraper()
        assert scraper._parse_liepin_markdown("") == []


class TestNormalizeCity:
    def test_splits_on_dash(self) -> None:
        assert _normalize_city("北京-朝阳区") == "北京"

    def test_splits_on_dot(self) -> None:
        assert _normalize_city("深圳·南山区") == "深圳"

    def test_splits_on_full_dot(self) -> None:
        assert _normalize_city("上海・浦东") == "上海"

    def test_splits_on_space(self) -> None:
        assert _normalize_city("广州 天河区") == "广州"

    def test_no_separator(self) -> None:
        assert _normalize_city("杭州") == "杭州"

    def test_empty(self) -> None:
        assert _normalize_city("") == ""


class TestMapLiepinScale:
    def test_exact_match(self) -> None:
        assert _map_liepin_scale("1000-9999人") == "1001-5000"

    def test_large_company(self) -> None:
        assert _map_liepin_scale("10000人以上") == "5001+"

    def test_small_company(self) -> None:
        assert _map_liepin_scale("1-49人") == "11-50"

    def test_medium_company(self) -> None:
        assert _map_liepin_scale("100-499人") == "51-200"

    def test_empty(self) -> None:
        assert _map_liepin_scale("") is None

    def test_unknown(self) -> None:
        assert _map_liepin_scale("custom value") is None

    def test_partial_match(self) -> None:
        # Test substring matching (e.g. "约100-499人")
        assert _map_liepin_scale("约100-499人左右") == "51-200"
