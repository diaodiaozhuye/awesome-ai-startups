"""GitHub API scraper for trending AI/ML projects and their organizations."""

from __future__ import annotations

import logging
import os

import httpx

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)


class GitHubTrendingScraper(BaseScraper):
    """Scrape GitHub for trending AI/ML organizations using the Search API.

    Uses the GitHub REST API to search for repositories tagged with AI/ML
    topics, then extracts organization information.

    Requires: GITHUB_TOKEN env var (optional but recommended for higher rate limits).
    """

    SEARCH_QUERIES = [
        "topic:artificial-intelligence stars:>500",
        "topic:machine-learning stars:>500",
        "topic:large-language-model stars:>200",
        "topic:generative-ai stars:>200",
    ]

    @property
    def source_name(self) -> str:
        return "github"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        token = os.environ.get("GITHUB_TOKEN", "")
        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"

        client = create_http_client()
        if headers:
            client.headers.update(headers)

        seen_orgs: set[str] = set()
        products: list[ScrapedProduct] = []

        try:
            for query in self.SEARCH_QUERIES:
                if len(products) >= limit:
                    break

                response = client.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": min(30, limit - len(products)),
                    },
                )
                response.raise_for_status()
                data = response.json()

                for repo in data.get("items", []):
                    owner = repo.get("owner", {})
                    org_login = owner.get("login", "")
                    org_type = owner.get("type", "")

                    if org_type != "Organization" or org_login in seen_orgs:
                        continue

                    seen_orgs.add(org_login)

                    try:
                        org_response = client.get(
                            f"https://api.github.com/orgs/{org_login}"
                        )
                        org_data = (
                            org_response.json() if org_response.is_success else {}
                        )
                    except (httpx.HTTPError, httpx.TimeoutException, OSError) as exc:
                        logger.debug(
                            "GitHub org fetch failed for %s: %s", org_login, exc
                        )
                        org_data = {}

                    twitter = org_data.get("twitter_username")
                    extra: dict[str, str] = {}
                    if twitter:
                        extra["twitter"] = f"@{twitter}"

                    product = ScrapedProduct(
                        name=org_data.get("name") or org_login,
                        source="github",
                        source_url=f"https://github.com/{org_login}",
                        source_tier=SourceTier.T2_OPEN_WEB,
                        company_website=org_data.get("blog") or None,
                        description=org_data.get("description")
                        or repo.get("description"),
                        company_headquarters_city=org_data.get("location"),
                        repository_url=f"https://github.com/{org_login}",
                        open_source=True,
                        tags=("open-source",),
                        extra=extra,
                    )
                    products.append(product)

                    if len(products) >= limit:
                        break
        finally:
            client.close()

        return products[:limit]
