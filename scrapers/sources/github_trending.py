"""GitHub API scraper for trending AI/ML projects and their organizations."""

from __future__ import annotations

import os

from scrapers.base import BaseScraper, ScrapedCompany
from scrapers.utils import create_http_client


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

    def scrape(self, limit: int = 100) -> list[ScrapedCompany]:
        token = os.environ.get("GITHUB_TOKEN", "")
        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"

        client = create_http_client()
        if headers:
            client.headers.update(headers)

        seen_orgs: set[str] = set()
        companies: list[ScrapedCompany] = []

        try:
            for query in self.SEARCH_QUERIES:
                if len(companies) >= limit:
                    break

                response = client.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": min(30, limit - len(companies)),
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

                    org_response = client.get(
                        f"https://api.github.com/orgs/{org_login}"
                    )
                    org_data = org_response.json() if org_response.is_success else {}

                    company = ScrapedCompany(
                        name=org_data.get("name") or org_login,
                        source="github",
                        source_url=f"https://github.com/{org_login}",
                        website=org_data.get("blog") or None,
                        description=org_data.get("description")
                        or repo.get("description"),
                        headquarters_city=org_data.get("location"),
                        github_url=f"https://github.com/{org_login}",
                        twitter=org_data.get("twitter_username"),
                        open_source=True,
                        tags=("open-source",),
                    )
                    companies.append(company)

                    if len(companies) >= limit:
                        break
        finally:
            client.close()

        return companies[:limit]
