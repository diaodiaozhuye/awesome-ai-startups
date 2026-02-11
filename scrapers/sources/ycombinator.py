"""Y Combinator company directory scraper."""

from __future__ import annotations

from scrapers.base import BaseScraper, ScrapedCompany
from scrapers.utils import create_http_client


class YCombinatorScraper(BaseScraper):
    """Scrape the Y Combinator company directory for AI startups.

    Uses the public YC API endpoint that powers their company directory.
    Filters for AI-related companies by searching relevant keywords.
    """

    YC_API_URL = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/YCCompany_production"
    YC_APP_ID = "45BWZJ1SGC"
    YC_API_KEY = "MjBjYjRiMzY0NzdhZWY0NjExY2NhZjYxMGIxYjc2MTAwNWFkNTkwNTc4NjgxYjU0YzFhYTY2ZGQ5OGY5NDMxZnJlc3RyaWN0SW5kaWNlcz0lNUIlMjJZQ0NvbXBhbnlfcHJvZHVjdGlvbiUyMiU1RCZ0YWdGaWx0ZXJzPSU1QiUyMiUyMiU1RCZhbmFseXRpY3NUYWdzPSU1QiUyMnljZGMlMjIlNUQ="

    AI_KEYWORDS = [
        "artificial intelligence",
        "machine learning",
        "AI",
        "LLM",
        "NLP",
        "computer vision",
    ]

    @property
    def source_name(self) -> str:
        return "ycombinator"

    def scrape(self, limit: int = 100) -> list[ScrapedCompany]:
        client = create_http_client()
        companies: list[ScrapedCompany] = []

        try:
            for keyword in self.AI_KEYWORDS:
                if len(companies) >= limit:
                    break

                response = client.get(
                    self.YC_API_URL,
                    params={
                        "query": keyword,
                        "hitsPerPage": min(20, limit - len(companies)),
                    },
                    headers={
                        "X-Algolia-Application-Id": self.YC_APP_ID,
                        "X-Algolia-API-Key": self.YC_API_KEY,
                    },
                )

                if not response.is_success:
                    continue

                data = response.json()
                seen_names: set[str] = {c.name.lower() for c in companies}

                for hit in data.get("hits", []):
                    name = hit.get("name", "")
                    if not name or name.lower() in seen_names:
                        continue

                    seen_names.add(name.lower())

                    location_parts = []
                    if hit.get("city"):
                        location_parts.append(hit["city"])
                    if hit.get("state"):
                        location_parts.append(hit["state"])

                    company = ScrapedCompany(
                        name=name,
                        source="ycombinator",
                        source_url=f"https://www.ycombinator.com/companies/{hit.get('slug', '')}",
                        website=hit.get("website") or None,
                        description=hit.get("one_liner") or hit.get("long_description"),
                        headquarters_city=hit.get("city"),
                        headquarters_country=hit.get("country") or "United States",
                        founded_year=hit.get("year_founded"),
                        tags=("ycombinator",),
                    )
                    companies.append(company)

                    if len(companies) >= limit:
                        break
        finally:
            client.close()

        return companies[:limit]
