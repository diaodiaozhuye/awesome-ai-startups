"""Google Play and Apple App Store scrapers for mobile AI apps.

T2 Open Web — search app stores for AI-related applications,
extracting ratings, download counts, and store URLs. Uses
google-play-scraper library for Google Play and iTunes Search API
(via httpx) for Apple App Store.
"""

from __future__ import annotations

import logging
import time

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.config import DEFAULT_REQUEST_DELAY

logger = logging.getLogger(__name__)

# AI-related search terms for app store discovery
_SEARCH_QUERIES = [
    "AI chatbot",
    "AI assistant",
    "AI image generator",
    "AI writing",
    "AI code",
    "ChatGPT",
    "AI photo editor",
    "AI translator",
    "AI voice",
    "AI art",
    "AI video",
    "text to image AI",
    "AI productivity",
    "AI scanner",
    "AI music",
]

# Known non-AI apps that show up in AI searches
_SKIP_BUNDLES = frozenset(
    {
        "com.google.android.googlequicksearchbox",
        "com.google.android.apps.photos",
        "com.apple.mobilesafari",
    }
)


class GooglePlayScraper(BaseScraper):
    """Scrape Google Play for AI-related mobile applications.

    Uses the google-play-scraper library to search for apps by
    AI-related keywords and extract metadata (rating, installs, etc.).
    """

    @property
    def source_name(self) -> str:
        return "google_play"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Search Google Play for AI apps."""
        try:
            from google_play_scraper import search as gp_search
        except ImportError:
            logger.info(
                "google-play-scraper not installed. "
                "Install with: pip install google-play-scraper"
            )
            return []

        products: list[ScrapedProduct] = []
        seen_ids: set[str] = set()

        for query in _SEARCH_QUERIES:
            if len(products) >= limit:
                break

            logger.debug("Google Play: searching '%s'", query)
            try:
                results = gp_search(
                    query,
                    lang="en",
                    country="us",
                    n_hits=20,
                )
            except Exception as e:
                logger.debug("Google Play search '%s' failed: %s", query, e)
                time.sleep(DEFAULT_REQUEST_DELAY)
                continue

            for app in results:
                app_id = app.get("appId", "")
                if not app_id or app_id in seen_ids:
                    continue
                if app_id in _SKIP_BUNDLES:
                    continue

                seen_ids.add(app_id)

                title = app.get("title", "").strip()
                if not title:
                    continue

                developer = app.get("developer", "")
                score = app.get("score")
                installs = app.get("realInstalls") or app.get("installs", "")
                icon = app.get("icon", "")
                description = app.get("summary") or app.get("description", "")
                url = f"https://play.google.com/store/apps/details?id={app_id}"

                # Truncate description
                if description and len(description) > 500:
                    description = description[:497] + "..."

                extra: dict[str, str] = {"google_play_app_id": app_id}
                if score is not None:
                    extra["google_play_rating"] = f"{score:.1f}"
                if installs:
                    extra["google_play_installs"] = str(installs)

                products.append(
                    ScrapedProduct(
                        name=title,
                        source=self.source_name,
                        source_url=url,
                        source_tier=SourceTier.T2_OPEN_WEB,
                        product_url=url,
                        icon_url=icon if icon else None,
                        description=description if description else None,
                        product_type="app",
                        category="ai-app",
                        company_name=developer if developer else None,
                        platforms=("android",),
                        status="active",
                        extra=extra,
                    )
                )

                if len(products) >= limit:
                    break

            time.sleep(DEFAULT_REQUEST_DELAY)

        logger.info("Google Play: discovered %d apps", len(products))
        return products


class AppStoreScraper(BaseScraper):
    """Scrape Apple App Store for AI-related mobile applications.

    Uses the iTunes Search API (free, no auth required) to find
    AI apps and extract metadata.
    """

    @property
    def source_name(self) -> str:
        return "app_store"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Search Apple App Store for AI apps via iTunes Search API."""
        from scrapers.utils import create_http_client

        client = create_http_client()
        products: list[ScrapedProduct] = []
        seen_ids: set[str] = set()

        try:
            for query in _SEARCH_QUERIES:
                if len(products) >= limit:
                    break

                logger.debug("App Store: searching '%s'", query)
                try:
                    response = client.get(
                        "https://itunes.apple.com/search",
                        params={
                            "term": query,
                            "entity": "software",
                            "country": "us",
                            "limit": 20,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                except Exception as e:
                    logger.debug("App Store search '%s' failed: %s", query, e)
                    time.sleep(DEFAULT_REQUEST_DELAY)
                    continue

                for app in data.get("results", []):
                    track_id = str(app.get("trackId", ""))
                    if not track_id or track_id in seen_ids:
                        continue

                    seen_ids.add(track_id)

                    name = app.get("trackName", "").strip()
                    if not name:
                        continue

                    developer = app.get("artistName", "")
                    rating = app.get("averageUserRating")
                    rating_count = app.get("userRatingCount")
                    icon = app.get("artworkUrl512") or app.get("artworkUrl100", "")
                    description = app.get("description", "")
                    store_url = app.get("trackViewUrl", "")

                    if description and len(description) > 500:
                        description = description[:497] + "..."

                    extra: dict[str, str] = {"app_store_track_id": track_id}
                    if rating is not None:
                        extra["app_store_rating"] = f"{rating:.1f}"
                    if rating_count is not None:
                        extra["app_store_rating_count"] = str(rating_count)

                    products.append(
                        ScrapedProduct(
                            name=name,
                            source=self.source_name,
                            source_url=store_url
                            or f"https://apps.apple.com/app/id{track_id}",
                            source_tier=SourceTier.T2_OPEN_WEB,
                            product_url=store_url if store_url else None,
                            icon_url=icon if icon else None,
                            description=description if description else None,
                            product_type="app",
                            category="ai-app",
                            company_name=developer if developer else None,
                            platforms=("ios",),
                            status="active",
                            extra=extra,
                        )
                    )

                    if len(products) >= limit:
                        break

                time.sleep(DEFAULT_REQUEST_DELAY)

        finally:
            client.close()

        logger.info("App Store: discovered %d apps", len(products))
        return products
