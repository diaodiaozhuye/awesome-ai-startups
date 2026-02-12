"""Tests for Chinese HTTP utilities (china_http.py)."""

from __future__ import annotations

from unittest.mock import patch

from scrapers.utils.china_http import (
    _HEADER_WORDS,
    _SKIP_WORDS,
    _is_table_header,
    _looks_like_salary,
    create_china_http_client,
    parse_chinese_job_markdown,
    random_user_agent,
)


class TestRandomUserAgent:
    def test_returns_string(self) -> None:
        ua = random_user_agent()
        assert isinstance(ua, str)
        assert len(ua) > 20

    def test_returns_browser_ua(self) -> None:
        ua = random_user_agent()
        assert "Mozilla" in ua

    def test_rotates(self) -> None:
        """Multiple calls should eventually return different UAs."""
        agents = {random_user_agent() for _ in range(50)}
        assert len(agents) > 1


class TestCreateChinaHttpClient:
    def test_creates_client(self) -> None:
        client = create_china_http_client()
        try:
            assert client is not None
            assert "zh-CN" in client.headers.get("Accept-Language", "")
            assert "Mozilla" in client.headers.get("User-Agent", "")
        finally:
            client.close()

    def test_sets_referer(self) -> None:
        client = create_china_http_client(referer="https://www.zhipin.com/")
        try:
            assert client.headers.get("Referer") == "https://www.zhipin.com/"
        finally:
            client.close()

    def test_no_referer_by_default(self) -> None:
        client = create_china_http_client()
        try:
            assert "Referer" not in client.headers
        finally:
            client.close()

    def test_proxy_from_env(self) -> None:
        with patch.dict("os.environ", {"CHINA_PROXY_URL": "http://proxy:8080"}):
            client = create_china_http_client()
            try:
                # Verify client was created (proxy is internal to httpx)
                assert client is not None
            finally:
                client.close()

    def test_custom_timeout(self) -> None:
        client = create_china_http_client(timeout=10.0)
        try:
            assert client.timeout.read == 10.0
        finally:
            client.close()


class TestParseChineseJobMarkdown:
    def test_empty_input(self) -> None:
        assert parse_chinese_job_markdown("") == []
        assert parse_chinese_job_markdown("short") == []

    def test_heading_pattern(self) -> None:
        """Test parsing job listings with heading-based format."""
        md = """
## [大模型算法工程师](https://example.com/job/1)
智谱华章科技·北京·1000-9999人

## [计算机视觉研究员](https://example.com/job/2)
腾讯·深圳·10000人以上

## [自然语言处理工程师](https://example.com/job/3)
百度·北京·10000人以上
"""
        jobs = parse_chinese_job_markdown(md)
        assert len(jobs) >= 3
        assert any("智谱" in j["company_name"] for j in jobs)

    def test_table_pattern(self) -> None:
        """Test parsing job listings with table format."""
        md = """
| 职位 | 公司 | 地点 |
| --- | --- | --- |
| ML Engineer | OpenAI | San Francisco |
| AI Researcher | Anthropic | London |
| Data Scientist | DeepMind | London |
"""
        jobs = parse_chinese_job_markdown(md)
        # Table header row should be skipped
        company_names = [j["company_name"] for j in jobs]
        assert "公司" not in company_names
        assert len(jobs) >= 2

    def test_card_pattern(self) -> None:
        """Test parsing job listings with bold card format."""
        # Markdown must be >100 chars to avoid early return guard
        md = (
            "This is a job listing page with many results from the search.\n"
            "Below are the AI-related job positions found:\n\n"
            "**大模型算法工程师**\n"
            "智谱华章·北京·15-30K\n\n"
            "**深度学习研究员**\n"
            "百度·北京·20-40K\n\n"
            "**NLP工程师**\n"
            "阿里巴巴·杭州·25-50K\n"
        )
        assert len(md) > 100, f"Test markdown too short: {len(md)}"
        jobs = parse_chinese_job_markdown(md)
        assert len(jobs) >= 2

    def test_skips_navigation_elements(self) -> None:
        """Skip elements that look like nav links."""
        md = """
## 首页
登录

## [大模型工程师](https://example.com/job/1)
智谱华章·北京
"""
        jobs = parse_chinese_job_markdown(md)
        company_names = [j["company_name"] for j in jobs]
        assert "首页" not in company_names
        assert "登录" not in company_names

    def test_max_size_truncation(self) -> None:
        """Input exceeding _MAX_MARKDOWN_SIZE should be truncated."""
        huge = "x" * 600_000
        # Should not raise or take too long
        result = parse_chinese_job_markdown(huge)
        assert isinstance(result, list)


class TestLooksLikeSalary:
    def test_salary_with_k(self) -> None:
        assert _looks_like_salary("15-30K") is True
        assert _looks_like_salary("20k") is True

    def test_salary_with_wan(self) -> None:
        assert _looks_like_salary("3-5万") is True

    def test_salary_range(self) -> None:
        assert _looks_like_salary("15000-25000") is True

    def test_salary_months(self) -> None:
        assert _looks_like_salary("13薪") is True

    def test_negotiable(self) -> None:
        assert _looks_like_salary("面议") is True

    def test_not_salary(self) -> None:
        assert _looks_like_salary("北京") is False
        assert _looks_like_salary("人工智能") is False
        assert _looks_like_salary("") is False


class TestIsTableHeader:
    def test_header_row(self) -> None:
        assert _is_table_header("职位", "公司") is True
        assert _is_table_header("job", "company") is True
        # "---" stripped of dashes becomes "", not in _HEADER_WORDS
        assert _is_table_header("---", "---") is False
        assert _is_table_header("title", "company") is True

    def test_data_row(self) -> None:
        assert _is_table_header("ML Engineer", "OpenAI") is False
        assert _is_table_header("大模型工程师", "智谱华章") is False


class TestConstants:
    def test_skip_words_contains_navigation(self) -> None:
        assert "首页" in _SKIP_WORDS
        assert "登录" in _SKIP_WORDS
        assert "注册" in _SKIP_WORDS

    def test_header_words_contains_headers(self) -> None:
        assert "职位" in _HEADER_WORDS
        assert "公司" in _HEADER_WORDS
        assert "job" in _HEADER_WORDS
