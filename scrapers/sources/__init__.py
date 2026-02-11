"""Scraper source implementations."""

from scrapers.sources.aijobs import AIJobsScraper
from scrapers.sources.crunchbase import CrunchbaseScraper
from scrapers.sources.github_trending import GitHubTrendingScraper
from scrapers.sources.glassdoor import GlassdoorScraper
from scrapers.sources.indeed import IndeedScraper
from scrapers.sources.lagou import LagouScraper
from scrapers.sources.liepin import LiepinScraper
from scrapers.sources.linkedin_jobs import LinkedInJobsScraper
from scrapers.sources.producthunt import ProductHuntScraper
from scrapers.sources.techcrunch import TechCrunchScraper
from scrapers.sources.ycombinator import YCombinatorScraper
from scrapers.sources.zhipin import ZhipinScraper

ALL_SCRAPERS = {
    # Original sources
    "github": GitHubTrendingScraper,
    "ycombinator": YCombinatorScraper,
    "producthunt": ProductHuntScraper,
    "crunchbase": CrunchbaseScraper,
    "techcrunch": TechCrunchScraper,
    # Job site scrapers
    "indeed": IndeedScraper,
    "aijobs": AIJobsScraper,
    "linkedin-jobs": LinkedInJobsScraper,
    "glassdoor": GlassdoorScraper,
    "zhipin": ZhipinScraper,
    "lagou": LagouScraper,
    "liepin": LiepinScraper,
}

__all__ = [
    "ALL_SCRAPERS",
    "AIJobsScraper",
    "CrunchbaseScraper",
    "GitHubTrendingScraper",
    "GlassdoorScraper",
    "IndeedScraper",
    "LagouScraper",
    "LiepinScraper",
    "LinkedInJobsScraper",
    "ProductHuntScraper",
    "TechCrunchScraper",
    "YCombinatorScraper",
    "ZhipinScraper",
]
