"""HTTP utilities for Chinese job site scrapers.

Provides User-Agent rotation, proxy support, and Chinese-specific
HTTP headers for scraping Boss直聘, 猎聘, and 拉勾.

Proxy configuration:
    Set ``CHINA_PROXY_URL`` environment variable to route requests
    through a proxy (e.g. ``http://proxy.example.com:8080``).
    Most Chinese job sites work fine without a proxy when using
    slow-and-steady request rates (7-10s delays).
"""

from __future__ import annotations

import os
import random
import re

import httpx

# Browser User-Agent strings for rotation
_USER_AGENTS = (
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
)

# Chinese-specific Accept-Language header
_ACCEPT_LANGUAGE = "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"


def random_user_agent() -> str:
    """Return a random browser User-Agent string."""
    return random.choice(_USER_AGENTS)  # noqa: S311


def create_china_http_client(
    *,
    referer: str = "",
    timeout: float = 30.0,
) -> httpx.Client:
    """Create an httpx client configured for Chinese job sites.

    Features:
      - Random User-Agent from rotation pool
      - Chinese Accept-Language header
      - Optional proxy via ``CHINA_PROXY_URL`` environment variable
      - Configurable referer header

    Args:
        referer: Referer header value (e.g. site homepage).
        timeout: Request timeout in seconds.

    Returns:
        Configured httpx.Client (caller must close).
    """
    headers: dict[str, str] = {
        "User-Agent": random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": _ACCEPT_LANGUAGE,
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
    }
    if referer:
        headers["Referer"] = referer

    proxy_url = os.environ.get("CHINA_PROXY_URL", "")

    return httpx.Client(
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
        proxy=proxy_url or None,
    )


def parse_chinese_job_markdown(
    markdown: str,
    *,
    site_name: str = "",
) -> list[dict[str, str]]:
    """Parse job listings from Firecrawl markdown output for Chinese job sites.

    Works across Boss直聘, 猎聘, and 拉勾 by looking for common patterns
    in Firecrawl's markdown conversion of job listing pages.

    Returns a list of dicts with keys:
      company_name, location, job_title, salary, scale, industry
    """
    if not markdown or len(markdown) < 100:
        return []

    # Truncate oversized input to prevent ReDoS
    if len(markdown) > _MAX_MARKDOWN_SIZE:
        markdown = markdown[:_MAX_MARKDOWN_SIZE]

    jobs: list[dict[str, str]] = []

    for match in _HEADING_PATTERN.finditer(markdown):
        job = _extract_job_fields(
            title=match.group(1).strip(),
            company_line=match.group(2).strip(),
            extra1=(match.group(3) or "").strip(),
            extra2=(match.group(4) or "").strip(),
        )
        if job:
            jobs.append(job)

    if len(jobs) < 3:
        for match in _TABLE_PATTERN.finditer(markdown):
            title = match.group(1).strip()
            company = match.group(2).strip()
            location = match.group(3).strip()

            if _is_table_header(title, company):
                continue

            jobs.append({
                "company_name": company,
                "location": location,
                "job_title": title,
                "salary": "",
                "scale": "",
                "industry": "",
            })

    if len(jobs) < 3:
        for match in _CARD_PATTERN.finditer(markdown):
            job = _extract_job_fields(
                title=match.group(1).strip(),
                company_line=match.group(2).strip(),
                extra1=(match.group(3) or "").strip(),
                extra2="",
            )
            if job:
                jobs.append(job)

    return jobs


def _extract_job_fields(
    title: str, company_line: str, extra1: str, extra2: str
) -> dict[str, str] | None:
    """Extract structured fields from raw parsed strings."""
    company_name = company_line.strip()

    if not company_name or len(company_name) < 2:
        return None

    # Skip navigation / non-job elements
    if company_name in _SKIP_WORDS or title in _SKIP_WORDS:
        return None

    # Determine which extra field is location vs salary
    location = ""
    salary = ""
    for field in (extra1, extra2):
        if not field:
            continue
        if _looks_like_salary(field):
            salary = field
        elif not location:
            location = field

    return {
        "company_name": company_name,
        "location": location,
        "job_title": title,
        "salary": salary,
        "scale": "",
        "industry": "",
    }


_SALARY_PATTERN = re.compile(r"\d+[kK万]|\d+-\d+|\d+薪|面议")

_SKIP_WORDS = frozenset(
    {"首页", "登录", "注册", "搜索", "推荐", "热门", "---", "职位", "公司"}
)

_HEADER_WORDS = frozenset(
    {"职位", "岗位", "公司", "企业", "job", "company", "---", "title"}
)

# Compiled regex patterns for markdown parsing (module-level for performance)
_HEADING_PATTERN = re.compile(
    r"(?:^|\n)#{1,4}\s+\[?([^\]\n]{3,60})\]?"
    r"(?:\([^)]*\))?\s*\n"
    r"([^\n]{2,40})"
    r"(?:\s*[·|•\-]\s*([^\n]{2,30}))?"
    r"(?:\s*[·|•\-]\s*([^\n]{2,30}))?",
    re.MULTILINE,
)

_TABLE_PATTERN = re.compile(
    r"\|\s*([^|]{3,50})\s*\|\s*([^|]{2,40})\s*\|\s*([^|]{2,30})\s*\|",
    re.MULTILINE,
)

_CARD_PATTERN = re.compile(
    r"\*\*([^*]{3,60})\*\*\s*\n"
    r"\s*([^\n·|•\-]{2,40})"
    r"(?:\s*[·|•\-]\s*([^\n]{2,30}))?",
    re.MULTILINE,
)

# Max markdown size to process (prevent ReDoS on pathological input)
_MAX_MARKDOWN_SIZE = 500_000


def _looks_like_salary(text: str) -> bool:
    """Heuristic: does this text look like a salary string?"""
    return bool(_SALARY_PATTERN.search(text))


def _is_table_header(col1: str, col2: str) -> bool:
    """Check if table row is a header row."""
    return col1.lower().strip(" -") in _HEADER_WORDS or col2.lower().strip(" -") in _HEADER_WORDS
