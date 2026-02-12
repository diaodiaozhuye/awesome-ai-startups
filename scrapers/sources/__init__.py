"""Scraper source implementations."""

from scrapers.sources.aijobs import AIJobsScraper
from scrapers.sources.arxiv_scraper import ArXivScraper
from scrapers.sources.company_website import CompanyWebsiteScraper
from scrapers.sources.crunchbase import CrunchbaseScraper
from scrapers.sources.huggingface import HuggingFaceScraper
from scrapers.sources.indeed import IndeedScraper
from scrapers.sources.lagou import LagouScraper
from scrapers.sources.liepin import LiepinScraper
from scrapers.sources.lmsys import LMSYSScraper
from scrapers.sources.openrouter import OpenRouterScraper
from scrapers.sources.package_registries import (
    DockerHubScraper,
    NpmScraper,
    PyPIScraper,
)
from scrapers.sources.producthunt import ProductHuntScraper
from scrapers.sources.techcrunch import TechCrunchScraper
from scrapers.sources.wikidata import WikidataScraper
from scrapers.sources.ycombinator import YCombinatorScraper
from scrapers.sources.zhipin import ZhipinScraper

ALL_SCRAPERS = {
    # T1 Authoritative
    "wikidata": WikidataScraper,
    "crunchbase": CrunchbaseScraper,
    # T2 Open Web — models & products
    "huggingface": HuggingFaceScraper,
    "ycombinator": YCombinatorScraper,
    "producthunt": ProductHuntScraper,
    "techcrunch": TechCrunchScraper,
    "arxiv": ArXivScraper,
    "lmsys": LMSYSScraper,
    "openrouter": OpenRouterScraper,
    # T2 Open Web — enrichment (package registries)
    "pypi": PyPIScraper,
    "npm": NpmScraper,
    "dockerhub": DockerHubScraper,
    # T2 Open Web — company websites
    "company_website": CompanyWebsiteScraper,
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
    "CompanyWebsiteScraper",
    "CrunchbaseScraper",
    "DockerHubScraper",
    "HuggingFaceScraper",
    "IndeedScraper",
    "LagouScraper",
    "LiepinScraper",
    "LMSYSScraper",
    "NpmScraper",
    "OpenRouterScraper",
    "ProductHuntScraper",
    "PyPIScraper",
    "TechCrunchScraper",
    "WikidataScraper",
    "YCombinatorScraper",
    "ZhipinScraper",
]
