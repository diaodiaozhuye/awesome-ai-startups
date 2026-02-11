"""Data enrichment pipeline: normalize, deduplicate, merge."""

from scrapers.enrichment.deduplicator import Deduplicator
from scrapers.enrichment.merger import Merger
from scrapers.enrichment.normalizer import Normalizer

__all__ = ["Normalizer", "Deduplicator", "Merger"]
