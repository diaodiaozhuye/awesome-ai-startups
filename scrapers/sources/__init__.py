"""Scraper source implementations.

Scrapers are organized by role:
- DiscoveryScraper: Only discovers new products (names + URLs)
- EnrichmentScraper: Enriches existing products with additional data
- UnifiedScraper (BaseScraper): Does both discovery and full scraping
"""

from scrapers.sources.aibot import AiBotScraper
from scrapers.sources.ainav import AiNavScraper
from scrapers.sources.app_stores import AppStoreScraper, GooglePlayScraper
from scrapers.sources.artificial_analysis import ArtificialAnalysisScraper
from scrapers.sources.crunchbase import CrunchbaseScraper
from scrapers.sources.github_trending import GitHubTrendingScraper
from scrapers.sources.huggingface import HuggingFaceScraper
from scrapers.sources.lmsys import LMSYSScraper
from scrapers.sources.openrouter import OpenRouterScraper
from scrapers.sources.package_registries import (
    DockerHubScraper,
    NpmScraper,
    PyPIScraper,
)
from scrapers.sources.papers_with_code import PapersWithCodeScraper
from scrapers.sources.producthunt import ProductHuntScraper
from scrapers.sources.techcrunch import TechCrunchScraper
from scrapers.sources.theresanai import TAAScraper
from scrapers.sources.toolify import ToolifyScraper
from scrapers.sources.wikidata import WikidataScraper
from scrapers.sources.ycombinator import YCombinatorScraper

ALL_SCRAPERS = {
    # T1 Authoritative (EnrichmentScraper role)
    "wikidata": WikidataScraper,
    "crunchbase": CrunchbaseScraper,
    # T2 Open Web — Discovery role
    "producthunt": ProductHuntScraper,
    "github": GitHubTrendingScraper,
    "toolify": ToolifyScraper,
    "aibot": AiBotScraper,
    "ainav": AiNavScraper,
    "ycombinator": YCombinatorScraper,
    "techcrunch": TechCrunchScraper,
    # T2 Open Web — Unified role (discover + enrich)
    "huggingface": HuggingFaceScraper,
    "lmsys": LMSYSScraper,
    "openrouter": OpenRouterScraper,
    "theresanaiforthat": TAAScraper,
    "artificial_analysis": ArtificialAnalysisScraper,
    "papers_with_code": PapersWithCodeScraper,
    # T2 Open Web — Enrichment role (package registries)
    "pypi": PyPIScraper,
    "npm": NpmScraper,
    "dockerhub": DockerHubScraper,
    # T2 Open Web — Enrichment role (app stores)
    "google_play": GooglePlayScraper,
    "app_store": AppStoreScraper,
}

__all__ = [
    "ALL_SCRAPERS",
    "AiBotScraper",
    "AiNavScraper",
    "AppStoreScraper",
    "ArtificialAnalysisScraper",
    "CrunchbaseScraper",
    "DockerHubScraper",
    "GitHubTrendingScraper",
    "GooglePlayScraper",
    "HuggingFaceScraper",
    "LMSYSScraper",
    "NpmScraper",
    "OpenRouterScraper",
    "PapersWithCodeScraper",
    "ProductHuntScraper",
    "PyPIScraper",
    "TAAScraper",
    "TechCrunchScraper",
    "ToolifyScraper",
    "WikidataScraper",
    "YCombinatorScraper",
]
