"""Scraper source implementations."""

from scrapers.sources.aijobs import AIJobsScraper
from scrapers.sources.arxiv_scraper import ArXivScraper
from scrapers.sources.crunchbase import CrunchbaseScraper
from scrapers.sources.huggingface import HuggingFaceScraper
from scrapers.sources.indeed import IndeedScraper
from scrapers.sources.lagou import LagouScraper
from scrapers.sources.liepin import LiepinScraper
from scrapers.sources.lmsys import LMSYSScraper
from scrapers.sources.producthunt import ProductHuntScraper
from scrapers.sources.techcrunch import TechCrunchScraper
from scrapers.sources.wikidata import WikidataScraper
from scrapers.sources.ycombinator import YCombinatorScraper
from scrapers.sources.zhipin import ZhipinScraper

ALL_SCRAPERS = {
    # T1 Authoritative
    "wikidata": WikidataScraper,
    # T2 Open Web
    "huggingface": HuggingFaceScraper,
    "ycombinator": YCombinatorScraper,
    "producthunt": ProductHuntScraper,
    "crunchbase": CrunchbaseScraper,
    "techcrunch": TechCrunchScraper,
    "arxiv": ArXivScraper,
    "lmsys": LMSYSScraper,
    # T4 Job site scrapers
    "indeed": IndeedScraper,
    "aijobs": AIJobsScraper,
    "zhipin": ZhipinScraper,
    "lagou": LagouScraper,
    "liepin": LiepinScraper,
}

__all__ = [
    "ALL_SCRAPERS",
    "AIJobsScraper",
    "ArXivScraper",
    "CrunchbaseScraper",
    "HuggingFaceScraper",
    "IndeedScraper",
    "LagouScraper",
    "LiepinScraper",
    "LMSYSScraper",
    "ProductHuntScraper",
    "TechCrunchScraper",
    "WikidataScraper",
    "YCombinatorScraper",
    "ZhipinScraper",
]
