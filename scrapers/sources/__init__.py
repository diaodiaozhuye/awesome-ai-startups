"""Scraper source implementations."""

from scrapers.sources.crunchbase import CrunchbaseScraper
from scrapers.sources.github_trending import GitHubTrendingScraper
from scrapers.sources.producthunt import ProductHuntScraper
from scrapers.sources.techcrunch import TechCrunchScraper
from scrapers.sources.ycombinator import YCombinatorScraper

ALL_SCRAPERS = {
    "github": GitHubTrendingScraper,
    "ycombinator": YCombinatorScraper,
    "producthunt": ProductHuntScraper,
    "crunchbase": CrunchbaseScraper,
    "techcrunch": TechCrunchScraper,
}

__all__ = [
    "ALL_SCRAPERS",
    "GitHubTrendingScraper",
    "YCombinatorScraper",
    "ProductHuntScraper",
    "CrunchbaseScraper",
    "TechCrunchScraper",
]
