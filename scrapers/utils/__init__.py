"""Utility functions: slugify, HTTP client, retry logic."""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any

import httpx

from scrapers.config import HTTP_TIMEOUT, MAX_RETRIES, RETRY_DELAY, USER_AGENT


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug.

    >>> slugify("OpenAI")
    'openai'
    >>> slugify("Hugging Face")
    'hugging-face'
    >>> slugify("1X Technologies")
    '1x-technologies'
    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    text = text.strip("-")
    return text


def create_http_client(**kwargs: Any) -> httpx.Client:
    """Create a configured httpx client with default headers."""
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=kwargs.pop("timeout", HTTP_TIMEOUT),
        follow_redirects=True,
        **kwargs,
    )


def fetch_with_retry(
    url: str,
    *,
    client: httpx.Client | None = None,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY,
) -> httpx.Response:
    """Fetch a URL with retry logic for transient failures."""
    own_client = client is None
    if own_client:
        client = create_http_client()

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = client.get(url)
            response.raise_for_status()
            return response
        except (httpx.HTTPStatusError, httpx.TransportError) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))

    if own_client:
        client.close()

    raise last_error  # type: ignore[misc]


def normalize_url(url: str) -> str:
    """Normalize a URL by stripping trailing slashes and fragments."""
    url = url.strip()
    url = url.split("#")[0]
    url = url.rstrip("/")
    return url


def extract_domain(url: str) -> str:
    """Extract the domain from a URL.

    >>> extract_domain("https://www.openai.com/research")
    'openai.com'
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.lower()
