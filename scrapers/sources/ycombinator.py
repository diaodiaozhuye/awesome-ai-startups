"""Y Combinator company directory scraper.

T2 Open Web source — discovers AI startups from the YC directory
using the public Algolia-powered search API.
"""

from __future__ import annotations

import time

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.config import DEFAULT_REQUEST_DELAY
from scrapers.utils import create_http_client


class YCombinatorScraper(BaseScraper):
    """Scrape the Y Combinator company directory for AI startups.

    Uses the public YC API endpoint that powers their company directory.
    Filters for AI-related companies by searching relevant keywords.
    """

    YC_API_URL = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/YCCompany_production"
    YC_APP_ID = "45BWZJ1SGC"
    YC_API_KEY = (
        "MjBjYjRiMzY0NzdhZWY0NjExY2NhZjYxMGIxYjc2MTAwNWFkNTkwNTc4NjgxYjU0Y"
        "zFhYTY2ZGQ5OGY5NDMxZnJlc3RyaWN0SW5kaWNlcz0lNUIlMjJZQ0NvbXBhbnlfcH"
        "JvZHVjdGlvbiUyMiU1RCZ0YWdGaWx0ZXJzPSU1QiUyMiUyMiU1RCZhbmFseXRpY3N"
        "UYWdzPSU1QiUyMnljZGMlMjIlNUQ="
    )

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

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Search the YC directory for AI companies and return products."""
        client = create_http_client()
        products: list[ScrapedProduct] = []
        seen_names: set[str] = set()

        try:
            for keyword in self.AI_KEYWORDS:
                if len(products) >= limit:
                    break

                response = client.get(
                    self.YC_API_URL,
                    params={
                        "query": keyword,
                        "hitsPerPage": min(20, limit - len(products)),
                    },
                    headers={
                        "X-Algolia-Application-Id": self.YC_APP_ID,
                        "X-Algolia-API-Key": self.YC_API_KEY,
                    },
                )

                if not response.is_success:
                    continue

                data = response.json()

                for hit in data.get("hits", []):
                    name = hit.get("name", "")
                    if not name or name.lower() in seen_names:
                        continue

                    seen_names.add(name.lower())

                    yc_slug = hit.get("slug", "")
                    website = hit.get("website") or None

                    # Determine batch from YC data
                    batch = hit.get("batch", "")
                    tags = ["ycombinator"]
                    if batch:
                        tags.append(f"yc-{batch.lower()}")

                    product = ScrapedProduct(
                        name=name,
                        source="ycombinator",
                        source_url=f"https://www.ycombinator.com/companies/{yc_slug}",
                        source_tier=SourceTier.T2_OPEN_WEB,
                        product_url=website,
                        description=hit.get("one_liner") or hit.get("long_description"),
                        category="ai-app",
                        tags=tuple(tags),
                        company_name=name,
                        company_website=website,
                        company_founded_year=hit.get("year_founded"),
                        company_headquarters_city=hit.get("city"),
                        company_headquarters_country=(
                            hit.get("country") or "United States"
                        ),
                        company_employee_count_range=_team_size_to_range(
                            hit.get("team_size")
                        ),
                        status="active",
                    )
                    products.append(product)

                    if len(products) >= limit:
                        break

                time.sleep(DEFAULT_REQUEST_DELAY)
        finally:
            client.close()

        return products[:limit]


def _team_size_to_range(team_size: int | None) -> str | None:
    """Convert a YC team_size integer to an employee count range string."""
    if team_size is None:
        return None
    if team_size <= 10:
        return "1-10"
    if team_size <= 50:
        return "11-50"
    if team_size <= 200:
        return "51-200"
    if team_size <= 500:
        return "201-500"
    if team_size <= 1000:
        return "501-1000"
    return "1001-5000"
