"""Base scraper abstract class and ScrapedCompany data class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScrapedCompany:
    """Immutable data class representing a company discovered by a scraper.

    Only `name` and `source` are required — scrapers should fill in
    as many fields as they can, and the enrichment pipeline will handle
    normalization and merging.
    """

    name: str
    source: str
    source_url: str = ""
    website: str | None = None
    description: str | None = None
    description_zh: str | None = None
    category: str | None = None
    tags: tuple[str, ...] = ()
    founded_year: int | None = None
    headquarters_city: str | None = None
    headquarters_country: str | None = None
    headquarters_country_code: str | None = None
    total_raised_usd: float | None = None
    last_round: str | None = None
    employee_count_range: str | None = None
    founders: tuple[dict[str, str], ...] = ()
    github_url: str | None = None
    twitter: str | None = None
    linkedin_url: str | None = None
    open_source: bool | None = None
    products: tuple[dict[str, str], ...] = ()
    extra: dict[str, str] = field(default_factory=dict)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this data source (e.g., 'github', 'ycombinator')."""
        ...

    @abstractmethod
    def scrape(self, limit: int = 100) -> list[ScrapedCompany]:
        """Scrape companies from this source.

        Args:
            limit: Maximum number of companies to return.

        Returns:
            List of ScrapedCompany objects discovered.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} source={self.source_name!r}>"
