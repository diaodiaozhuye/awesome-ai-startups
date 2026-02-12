"""Tests for the Zhipin (Boss直聘) scraper with mocked HTTP responses."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scrapers.sources.zhipin import ZhipinScraper, _map_zhipin_scale, _normalize_city

_SAMPLE_HTML = """
<html><body>
<div class="search-job-result">
  <div class="job-card-wrapper">
    <span class="company-name"><a>北京智谱华章科技有限公司</a></span>
    <span class="job-area">北京·海淀区</span>
    <span class="job-name">大模型算法工程师</span>
    <ul class="company-tag-list">
      <li>人工智能</li>
      <li>1000-9999人</li>
    </ul>
  </div>
  <div class="job-card-wrapper">
    <span class="company-name"><a>深圳市腾讯计算机系统有限公司</a></span>
    <span class="job-area">深圳·南山区</span>
    <span class="job-name">计算机视觉研究员</span>
    <ul class="company-tag-list">
      <li>互联网</li>
      <li>10000人以上</li>
    </ul>
  </div>
</div>
</body></html>
"""


class TestZhipinSearchJobs:
    @patch("scrapers.sources.zhipin.create_china_http_client")
    def test_parses_chinese_job_cards_via_httpx(self, mock_create: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = _SAMPLE_HTML
        mock_response.is_success = True

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.headers = {}
        mock_create.return_value = mock_client

        scraper = ZhipinScraper()
        scraper.RATE_LIMIT_DELAY = 0.0
        # Test the httpx fallback path directly
        jobs = scraper._search_via_httpx("大模型", 10)

        assert len(jobs) == 2
        assert "智谱" in jobs[0]["company_name"]
        assert "腾讯" in jobs[1]["company_name"]


class TestZhipinExtractCompany:
    def test_extracts_chinese_company(self) -> None:
        scraper = ZhipinScraper()
        company = scraper._extract_company({
            "company_name": "北京智谱华章科技有限公司",
            "location": "北京·海淀区",
            "job_title": "大模型算法工程师",
            "scale": "1000-9999人",
            "industry": "人工智能",
        })
        assert company is not None
        assert company.name == "北京智谱华章科技有限公司"
        assert company.source == "zhipin"
        assert company.company_headquarters_city == "北京"
        assert company.company_headquarters_country == "China"
        assert company.company_headquarters_country_code == "CN"
        assert company.company_employee_count_range == "1001-5000"
        assert company.description_zh == "人工智能"
        assert company.extra.get("name_zh") == "北京智谱华章科技有限公司"

    def test_extracts_llm_category(self) -> None:
        scraper = ZhipinScraper()
        company = scraper._extract_company({
            "company_name": "TestCo",
            "location": "上海",
            "job_title": "大模型工程师",
            "scale": "",
            "industry": "",
        })
        assert company is not None
        assert company.category == "llm-foundation-model"

    def test_returns_none_for_empty(self) -> None:
        scraper = ZhipinScraper()
        assert scraper._extract_company({"company_name": ""}) is None


class TestNormalizeCity:
    def test_splits_on_dot(self) -> None:
        assert _normalize_city("北京·海淀区") == "北京"

    def test_splits_on_dash(self) -> None:
        assert _normalize_city("深圳-南山区") == "深圳"

    def test_no_separator(self) -> None:
        assert _normalize_city("上海") == "上海"

    def test_empty(self) -> None:
        assert _normalize_city("") == ""


class TestMapZhipinScale:
    def test_exact_match(self) -> None:
        assert _map_zhipin_scale("1000-9999人") == "1001-5000"

    def test_large_company(self) -> None:
        assert _map_zhipin_scale("10000人以上") == "5001+"

    def test_small_company(self) -> None:
        assert _map_zhipin_scale("0-20人") == "1-10"

    def test_empty(self) -> None:
        assert _map_zhipin_scale("") is None

    def test_unknown(self) -> None:
        assert _map_zhipin_scale("custom value") is None
