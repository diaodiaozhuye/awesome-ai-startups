"""Base scraper abstract class, SourceTier enum, and ScrapedProduct data class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum


class SourceTier(IntEnum):
    """Data source reliability tier.

    Each tier carries a trust score reflecting the expected accuracy
    and authority of data originating from that source class.
    """

    T1_AUTHORITATIVE = 1
    T2_OPEN_WEB = 2
    T3_AI_GENERATED = 3
    T4_AUXILIARY = 4

    @property
    def trust_score(self) -> float:
        """Return the trust score associated with this tier."""
        _scores: dict[int, float] = {
            1: 0.95,
            2: 0.75,
            3: 0.50,
            4: 0.20,
        }
        return _scores[self.value]


# ---------------------------------------------------------------------------
# Discovery-phase data
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiscoveredName:
    """A product name found during the discovery phase.

    Scrapers may implement ``discover()`` to return lightweight name records
    before performing full scrapes.
    """

    name: str
    source: str
    source_url: str = ""
    discovered_at: str = ""  # ISO-8601 date string


# ---------------------------------------------------------------------------
# Nested company info carried inside a ScrapedProduct
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Main scraper output
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScrapedProduct:
    """Immutable data class representing a product discovered by a scraper.

    Field layout mirrors ``product.schema.json``.  Only ``name`` and
    ``source`` are truly required -- scrapers should fill in as many fields
    as they can; the enrichment pipeline handles normalization and merging.

    Tuples are used in place of lists for frozen-dataclass compatibility.
    """

    # -- Required --------------------------------------------------------
    name: str
    source: str
    source_url: str = ""
    source_tier: SourceTier = SourceTier.T2_OPEN_WEB

    # -- Product identity ------------------------------------------------
    name_zh: str | None = None
    product_url: str | None = None
    icon_url: str | None = None
    description: str | None = None
    description_zh: str | None = None
    product_type: str | None = None
    category: str | None = None
    sub_category: str | None = None
    tags: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

    # -- Company (flat fields for scraper simplicity) --------------------
    company_name: str | None = None
    company_name_zh: str | None = None
    company_website: str | None = None
    company_wikipedia_url: str | None = None
    company_logo_url: str | None = None
    company_description: str | None = None
    company_founded_year: int | None = None
    company_headquarters_city: str | None = None
    company_headquarters_country: str | None = None
    company_headquarters_country_code: str | None = None
    company_total_raised_usd: float | None = None
    company_last_round: str | None = None
    company_employee_count_range: str | None = None

    # -- Key people ------------------------------------------------------
    key_people: tuple[dict[str, str | bool], ...] = ()

    # -- Tech specs ------------------------------------------------------
    architecture: str | None = None
    parameter_count: str | None = None
    context_window: int | None = None
    modalities: tuple[str, ...] = ()
    supported_languages: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ()
    api_available: bool | None = None
    api_docs_url: str | None = None

    # -- Open source -----------------------------------------------------
    open_source: bool | None = None
    license: str | None = None
    repository_url: str | None = None
    github_stars: int | None = None
    github_contributors: int | None = None

    # -- Pricing ---------------------------------------------------------
    pricing_model: str | None = None
    has_free_tier: bool | None = None

    # -- Market ----------------------------------------------------------
    target_audience: tuple[str, ...] = ()
    use_cases: tuple[str, ...] = ()

    # -- Relations -------------------------------------------------------
    competitors: tuple[str, ...] = ()
    based_on: tuple[str, ...] = ()

    # -- Status ----------------------------------------------------------
    status: str | None = None
    release_date: str | None = None

    # -- Hiring (flat fields for scraper simplicity) ---------------------
    hiring_positions: tuple[dict[str, str], ...] = ()
    hiring_tech_stack: tuple[str, ...] = ()

    # -- Extra -----------------------------------------------------------
    extra: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Wrap mutable extra dict in MappingProxyType for true immutability."""
        from types import MappingProxyType as _MappingProxy

        if isinstance(self.extra, dict):
            object.__setattr__(self, "extra", _MappingProxy(self.extra))


# ---------------------------------------------------------------------------
# Abstract base class for all scrapers
# ---------------------------------------------------------------------------


class BaseScraper(ABC):
    """Abstract base class for all scrapers.

    Subclasses must implement :pyattr:`source_name`, :pyattr:`source_tier`,
    and :meth:`scrape`.  Optionally override :meth:`discover` to support a
    lightweight name-discovery phase.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the canonical name of this data source (e.g. ``'github'``)."""
        ...

    @property
    @abstractmethod
    def source_tier(self) -> SourceTier:
        """Return the reliability tier of this data source."""
        ...

    @abstractmethod
    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape products from this source.

        Args:
            limit: Maximum number of products to return.

        Returns:
            List of :class:`ScrapedProduct` instances discovered.
        """
        ...

    def discover(self, limit: int = 100) -> list[DiscoveredName]:
        """Discover product names without performing a full scrape.

        The default implementation returns an empty list.  Scrapers that
        support a lightweight discovery phase should override this method.

        Args:
            limit: Maximum number of names to return.

        Returns:
            List of :class:`DiscoveredName` instances.
        """
        return []

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"source={self.source_name!r} "
            f"tier={self.source_tier.name}>"
        )


# ---------------------------------------------------------------------------
# Backwards compatibility
# ---------------------------------------------------------------------------

# Deprecated: use ScrapedProduct
ScrapedCompany = ScrapedProduct
