"""Data enrichment pipeline: normalize, deduplicate, merge, validate, score."""

from scrapers.enrichment.cross_validator import CrossValidationViolation, CrossValidator
from scrapers.enrichment.deduplicator import Deduplicator
from scrapers.enrichment.icon_fetcher import IconFetcher
from scrapers.enrichment.keyword_extractor import KeywordExtractor
from scrapers.enrichment.llm_enricher import LLMEnricher
from scrapers.enrichment.merger import Merger
from scrapers.enrichment.normalizer import Normalizer, PlausibilityValidator
from scrapers.enrichment.quality_scorer import QualityScorer

__all__ = [
    "CrossValidator",
    "CrossValidationViolation",
    "Normalizer",
    "Deduplicator",
    "Merger",
    "KeywordExtractor",
    "IconFetcher",
    "QualityScorer",
    "LLMEnricher",
    "PlausibilityValidator",
]
