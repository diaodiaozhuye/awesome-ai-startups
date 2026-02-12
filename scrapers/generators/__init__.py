"""Auto-generate index.json and stats.json from product data."""

from scrapers.generators.index_generator import IndexGenerator
from scrapers.generators.stats_generator import StatsGenerator

__all__ = ["IndexGenerator", "StatsGenerator"]
