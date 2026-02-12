"""Product Hunt GraphQL API scraper for AI products."""

from __future__ import annotations

import logging
import os

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)


class ProductHuntScraper(BaseScraper):
    """Scrape Product Hunt for AI-related products using their GraphQL API.

    Requires: PRODUCTHUNT_TOKEN env var for API access.
    """

    API_URL = "https://api.producthunt.com/v2/api/graphql"

    QUERY = """
    query($topic: String!, $first: Int!) {
      posts(topic: $topic, first: $first, order: VOTES) {
        edges {
          node {
            id
            name
            tagline
            description
            url
            website
            votesCount
            makers {
              name
            }
          }
        }
      }
    }
    """

    AI_TOPICS = ["artificial-intelligence", "machine-learning", "generative-ai"]

    @property
    def source_name(self) -> str:
        return "producthunt"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        token = os.environ.get("PRODUCTHUNT_TOKEN", "")
        if not token:
            logger.warning("PRODUCTHUNT_TOKEN not set, skipping.")
            return []

        client = create_http_client()
        client.headers["Authorization"] = f"Bearer {token}"

        products: list[ScrapedProduct] = []
        seen_names: set[str] = set()

        try:
            for topic in self.AI_TOPICS:
                if len(products) >= limit:
                    break

                response = client.post(
                    self.API_URL,
                    json={
                        "query": self.QUERY,
                        "variables": {
                            "topic": topic,
                            "first": min(20, limit - len(products)),
                        },
                    },
                )

                if not response.is_success:
                    continue

                data = response.json()
                posts = data.get("data", {}).get("posts", {}).get("edges", [])

                for edge in posts:
                    node = edge.get("node", {})
                    name = node.get("name", "")

                    if not name or name.lower() in seen_names:
                        continue

                    seen_names.add(name.lower())

                    makers = tuple(
                        {"name": m["name"], "title": "Maker", "is_founder": False}
                        for m in node.get("makers", [])
                        if m.get("name")
                    )

                    website = node.get("website")
                    product = ScrapedProduct(
                        name=name,
                        source="producthunt",
                        source_url=node.get("url", ""),
                        source_tier=SourceTier.T2_OPEN_WEB,
                        product_url=website,
                        company_website=website,
                        description=node.get("tagline") or node.get("description"),
                        key_people=makers,
                        tags=("generative-ai",),
                        status="active",
                    )
                    products.append(product)

                    if len(products) >= limit:
                        break
        finally:
            client.close()

        return products[:limit]
