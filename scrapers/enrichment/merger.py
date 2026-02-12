"""Tier-based field merger with provenance tracking.

Replaces the old non-destructive Merger with a tier-aware strategy:
  - T1 (authoritative) data can overwrite T2-T4 data.
  - Same-tier data keeps the existing value (first-come-first-served).
  - T3 (AI-generated) data only fills empty fields, never overwrites.
  - T4 (auxiliary) data only contributes to ``hiring.*`` fields and discovery.
  - Every field write records provenance: ``{source, tier, confidence, updated_at}``.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any
from urllib.parse import quote_plus

from scrapers.base import ScrapedProduct, SourceTier
from scrapers.config import PRODUCTS_DIR

logger = logging.getLogger(__name__)

# Fields that belong to the hiring namespace.  T4 sources may only write these.
_HIRING_FIELDS: frozenset[str] = frozenset(
    {
        "hiring.is_hiring",
        "hiring.total_positions",
        "hiring.positions",
        "hiring.tech_stack",
        "hiring.last_checked",
    }
)

# Top-level array fields that should be *extended* (union) rather than replaced.
_ARRAY_FIELDS: frozenset[str] = frozenset(
    {
        "tags",
        "keywords",
        "modalities",
        "supported_languages",
        "platforms",
        "target_audience",
        "use_cases",
        "integrations",
        "competitors",
        "based_on",
        "used_by",
        "key_people",
        "hiring.positions",
        "hiring.tech_stack",
        "company.funding.investors",
    }
)

# ---------------------------------------------------------------------------
# Field mapping: ScrapedProduct attribute -> product JSON path
# ---------------------------------------------------------------------------
_SCALAR_FIELD_MAP: dict[str, str] = {
    "name_zh": "name_zh",
    "product_url": "product_url",
    "icon_url": "icon_url",
    "description": "description",
    "description_zh": "description_zh",
    "product_type": "product_type",
    "category": "category",
    "sub_category": "sub_category",
    "company_name": "company.name",
    "company_name_zh": "company.name_zh",
    "company_website": "company.website",
    "company_wikipedia_url": "company.wikipedia_url",
    "company_logo_url": "company.logo_url",
    "company_description": "company.description",
    "company_founded_year": "company.founded_year",
    "company_headquarters_city": "company.headquarters.city",
    "company_headquarters_country": "company.headquarters.country",
    "company_headquarters_country_code": "company.headquarters.country_code",
    "company_total_raised_usd": "company.funding.total_raised_usd",
    "company_last_round": "company.funding.last_round",
    "company_employee_count_range": "company.employee_count_range",
    "architecture": "architecture",
    "parameter_count": "parameter_count",
    "context_window": "context_window",
    "open_source": "open_source",
    "license": "license",
    "repository_url": "repository_url",
    "github_stars": "github_stars",
    "github_contributors": "github_contributors",
    "api_available": "api_available",
    "api_docs_url": "api_docs_url",
    "pricing_model": "pricing.model",
    "has_free_tier": "pricing.has_free_tier",
    "status": "status",
    "release_date": "release_date",
}

_ARRAY_FIELD_MAP: dict[str, str] = {
    "tags": "tags",
    "keywords": "keywords",
    "modalities": "modalities",
    "supported_languages": "supported_languages",
    "platforms": "platforms",
    "target_audience": "target_audience",
    "use_cases": "use_cases",
    "competitors": "competitors",
    "based_on": "based_on",
    "key_people": "key_people",
    "hiring_positions": "hiring.positions",
    "hiring_tech_stack": "hiring.tech_stack",
}


# ---------------------------------------------------------------------------
# Helper: nested dict access by dotted path
# ---------------------------------------------------------------------------


def _get_nested(data: dict[str, Any], path: str) -> Any:
    """Retrieve a value from *data* following a dotted *path*.

    Returns ``None`` when any intermediate key is missing.
    """
    keys = path.split(".")
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _set_nested(data: dict[str, Any], path: str, value: Any) -> None:
    """Set a value inside *data* at the given dotted *path*.

    Intermediate dicts are created automatically.
    """
    keys = path.split(".")
    current = data
    for key in keys[:-1]:
        current = current.setdefault(key, {})
    current[keys[-1]] = value


# ---------------------------------------------------------------------------
# TieredMerger
# ---------------------------------------------------------------------------


class TieredMerger:
    """Merge scraped product data using tier-based priority with field-level provenance."""

    # -- public API ---------------------------------------------------------

    def merge_or_create(self, slug: str, scraped: ScrapedProduct) -> dict[str, Any]:
        """Merge into existing product or create new one.  Returns the product dict."""
        slug = self._validate_slug(slug)
        filepath = PRODUCTS_DIR / f"{slug}.json"
        if filepath.exists():
            return self.merge_update(slug, scraped)
        return self.create_new(slug, scraped)

    def merge_update(self, slug: str, scraped: ScrapedProduct) -> dict[str, Any]:
        """Merge scraped data into existing product JSON using tier rules."""
        slug = self._validate_slug(slug)
        filepath = PRODUCTS_DIR / f"{slug}.json"
        product: dict[str, Any] = json.loads(filepath.read_text(encoding="utf-8"))
        new_tier = scraped.source_tier.value

        # -- scalar fields --------------------------------------------------
        for attr, json_path in _SCALAR_FIELD_MAP.items():
            value = getattr(scraped, attr, None)
            if value is None:
                continue
            if not self._is_allowed_field(json_path, new_tier):
                continue
            self._set_field(product, json_path, value, scraped)

        # -- array fields (extend with unique values) -----------------------
        for attr, json_path in _ARRAY_FIELD_MAP.items():
            value = getattr(scraped, attr, None)
            if not value:
                continue
            if not self._is_allowed_field(json_path, new_tier):
                continue
            self._extend_array_field(product, json_path, value, scraped)

        # -- company.url fallback -------------------------------------------
        if _get_nested(product, "company.url") is None:
            _set_nested(product, "company.url", self._build_company_url(scraped))
            self._record_provenance(product, "company.url", scraped)

        # -- T4 hiring convenience: set is_hiring flag if positions present --
        if new_tier == SourceTier.T4_AUXILIARY and scraped.hiring_positions:
            self._set_field(product, "hiring.is_hiring", True, scraped)
            self._set_field(
                product,
                "hiring.last_checked",
                date.today().isoformat(),
                scraped,
            )

        # -- sources array (always append) ----------------------------------
        self._append_source(product, scraped)

        # -- meta.last_updated ----------------------------------------------
        product.setdefault("meta", {})["last_updated"] = date.today().isoformat()

        # -- persist --------------------------------------------------------
        self._write(filepath, product)
        return product

    def create_new(self, slug: str, scraped: ScrapedProduct) -> dict[str, Any]:
        """Create a new product JSON from scraped data."""
        slug = self._validate_slug(slug)
        today = date.today().isoformat()

        product: dict[str, Any] = {
            "slug": slug,
            "name": scraped.name,
            "product_url": scraped.product_url or "",
            "description": scraped.description or f"{scraped.name} is an AI product.",
            "product_type": scraped.product_type or "other",
            "category": scraped.category or "ai-app",
            "status": scraped.status or "active",
            "meta": {
                "added_date": today,
                "last_updated": today,
                "provenance": {},
            },
            "sources": [],
        }

        # -- optional i18n fields -------------------------------------------
        if scraped.name_zh:
            product["name_zh"] = scraped.name_zh
        if scraped.description_zh:
            product["description_zh"] = scraped.description_zh

        # -- company block --------------------------------------------------
        company_name = scraped.company_name or scraped.name
        company_url = self._build_company_url(scraped)
        product["company"] = {
            "name": company_name,
            "url": company_url,
        }
        if scraped.company_name_zh:
            product["company"]["name_zh"] = scraped.company_name_zh
        if scraped.company_website:
            product["company"]["website"] = scraped.company_website
        if scraped.company_wikipedia_url:
            product["company"]["wikipedia_url"] = scraped.company_wikipedia_url
        if scraped.company_logo_url:
            product["company"]["logo_url"] = scraped.company_logo_url
        if scraped.company_description:
            product["company"]["description"] = scraped.company_description
        if scraped.company_founded_year is not None:
            product["company"]["founded_year"] = scraped.company_founded_year
        if scraped.company_headquarters_city or scraped.company_headquarters_country:
            hq: dict[str, Any] = {}
            if scraped.company_headquarters_city:
                hq["city"] = scraped.company_headquarters_city
            if scraped.company_headquarters_country:
                hq["country"] = scraped.company_headquarters_country
            if scraped.company_headquarters_country_code:
                hq["country_code"] = scraped.company_headquarters_country_code
            product["company"]["headquarters"] = hq
        if scraped.company_total_raised_usd is not None or scraped.company_last_round:
            funding: dict[str, Any] = {}
            if scraped.company_total_raised_usd is not None:
                funding["total_raised_usd"] = scraped.company_total_raised_usd
            if scraped.company_last_round:
                funding["last_round"] = scraped.company_last_round
            product["company"]["funding"] = funding
        if scraped.company_employee_count_range:
            product["company"][
                "employee_count_range"
            ] = scraped.company_employee_count_range

        # -- icon -----------------------------------------------------------
        if scraped.icon_url:
            product["icon_url"] = scraped.icon_url

        # -- sub_category ---------------------------------------------------
        if scraped.sub_category:
            product["sub_category"] = scraped.sub_category

        # -- array fields ---------------------------------------------------
        if scraped.tags:
            product["tags"] = list(scraped.tags)
        if scraped.keywords:
            product["keywords"] = list(scraped.keywords)
        if scraped.key_people:
            product["key_people"] = [dict(p) for p in scraped.key_people]
        if scraped.modalities:
            product["modalities"] = list(scraped.modalities)
        if scraped.supported_languages:
            product["supported_languages"] = list(scraped.supported_languages)
        if scraped.platforms:
            product["platforms"] = list(scraped.platforms)
        if scraped.target_audience:
            product["target_audience"] = list(scraped.target_audience)
        if scraped.use_cases:
            product["use_cases"] = list(scraped.use_cases)
        if scraped.competitors:
            product["competitors"] = list(scraped.competitors)
        if scraped.based_on:
            product["based_on"] = list(scraped.based_on)

        # -- tech specs -----------------------------------------------------
        if scraped.architecture:
            product["architecture"] = scraped.architecture
        if scraped.parameter_count:
            product["parameter_count"] = scraped.parameter_count
        if scraped.context_window is not None:
            product["context_window"] = scraped.context_window
        if scraped.api_available is not None:
            product["api_available"] = scraped.api_available
        if scraped.api_docs_url:
            product["api_docs_url"] = scraped.api_docs_url

        # -- open source ----------------------------------------------------
        if scraped.open_source is not None:
            product["open_source"] = scraped.open_source
        if scraped.license:
            product["license"] = scraped.license
        if scraped.repository_url:
            product["repository_url"] = scraped.repository_url
        if scraped.github_stars is not None:
            product["github_stars"] = scraped.github_stars
        if scraped.github_contributors is not None:
            product["github_contributors"] = scraped.github_contributors

        # -- pricing --------------------------------------------------------
        if scraped.pricing_model or scraped.has_free_tier is not None:
            pricing: dict[str, Any] = {}
            if scraped.pricing_model:
                pricing["model"] = scraped.pricing_model
            if scraped.has_free_tier is not None:
                pricing["has_free_tier"] = scraped.has_free_tier
            product["pricing"] = pricing

        # -- status / release -----------------------------------------------
        if scraped.release_date:
            product["release_date"] = scraped.release_date

        # -- hiring ---------------------------------------------------------
        if scraped.hiring_positions or scraped.hiring_tech_stack:
            hiring: dict[str, Any] = {}
            if scraped.hiring_positions:
                hiring["is_hiring"] = True
                hiring["positions"] = [dict(p) for p in scraped.hiring_positions]
                hiring["total_positions"] = len(scraped.hiring_positions)
            if scraped.hiring_tech_stack:
                hiring["tech_stack"] = list(scraped.hiring_tech_stack)
            hiring["last_checked"] = today
            product["hiring"] = hiring

        # -- social (under company) -----------------------------------------
        social: dict[str, str] = {}
        if scraped.extra.get("linkedin_url"):
            social["linkedin"] = scraped.extra["linkedin_url"]
        if scraped.extra.get("twitter"):
            social["twitter"] = scraped.extra["twitter"]
        if scraped.extra.get("github_url"):
            social["github"] = scraped.extra["github_url"]
        if scraped.extra.get("crunchbase_url"):
            social["crunchbase"] = scraped.extra["crunchbase_url"]
        if social:
            product["company"]["social"] = social

        # -- provenance for all set fields ----------------------------------
        provenance_entry = self._build_provenance(scraped)
        provenance: dict[str, Any] = {}
        self._collect_paths(product, "", provenance, provenance_entry)
        product["meta"]["provenance"] = provenance

        # -- sources --------------------------------------------------------
        self._append_source(product, scraped)

        # -- persist --------------------------------------------------------
        filepath = PRODUCTS_DIR / f"{slug}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        self._write(filepath, product)
        return product

    # -- slug validation ----------------------------------------------------

    @staticmethod
    def _validate_slug(slug: str) -> str:
        """Validate slug to prevent path traversal.

        Raises:
            ValueError: If the slug is invalid or would escape PRODUCTS_DIR.
        """
        import re

        if not slug or not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", slug):
            raise ValueError(f"Invalid slug: {slug!r}")
        filepath = (PRODUCTS_DIR / f"{slug}.json").resolve()
        if not str(filepath).startswith(str(PRODUCTS_DIR.resolve())):
            raise ValueError(f"Slug would escape products directory: {slug!r}")
        return slug

    # -- tier logic ---------------------------------------------------------

    @staticmethod
    def _should_overwrite(existing_tier: int | None, new_tier: int) -> bool:
        """Determine if new data should overwrite existing based on tiers.

        Rules:
          - ``existing_tier is None`` (empty field) -> always fill.
          - Lower tier number = higher priority, so overwrite when ``new_tier < existing_tier``.
        """
        if existing_tier is None:
            return True
        return new_tier < existing_tier

    @staticmethod
    def _is_allowed_field(json_path: str, tier: int) -> bool:
        """Check whether a source tier is allowed to write to *json_path*.

        T4 sources may only write to ``hiring.*`` fields.
        """
        if tier == SourceTier.T4_AUXILIARY:
            return json_path in _HIRING_FIELDS
        return True

    # -- field setters ------------------------------------------------------

    def _set_field(
        self,
        product: dict[str, Any],
        field_path: str,
        value: Any,
        scraped: ScrapedProduct,
    ) -> bool:
        """Set a field if tier rules allow; update provenance.  Returns ``True`` if set."""
        new_tier = scraped.source_tier.value
        existing_tier = self._get_provenance_tier(product, field_path)
        existing_value = _get_nested(product, field_path)

        # T3 data only fills empty fields.
        if new_tier == SourceTier.T3_AI_GENERATED:
            if existing_value is not None and existing_value != "":
                return False

        if not self._should_overwrite(existing_tier, new_tier):
            return False

        _set_nested(product, field_path, value)
        self._record_provenance(product, field_path, scraped)
        return True

    def _extend_array_field(
        self,
        product: dict[str, Any],
        field_path: str,
        new_items: tuple[Any, ...] | list[Any],
        scraped: ScrapedProduct,
    ) -> bool:
        """Extend an array field with unique values.  Returns ``True`` if anything was added."""
        existing = _get_nested(product, field_path)
        if existing is None:
            existing = []

        if not isinstance(existing, list):
            existing = list(existing)

        # Build a set of serialized existing items for dedup.
        existing_serialized = {json.dumps(item, sort_keys=True) for item in existing}
        added = False
        for item in new_items:
            # Convert frozen sub-dicts (e.g. key_people) to plain dicts.
            if isinstance(item, dict):
                item = dict(item)
            serialized = json.dumps(item, sort_keys=True)
            if serialized not in existing_serialized:
                existing.append(item)
                existing_serialized.add(serialized)
                added = True

        if added:
            _set_nested(product, field_path, existing)
            self._record_provenance(product, field_path, scraped)
        return added

    # -- provenance helpers -------------------------------------------------

    @staticmethod
    def _build_provenance(scraped: ScrapedProduct) -> dict[str, Any]:
        """Build a provenance entry for a field."""
        return {
            "source": scraped.source,
            "tier": scraped.source_tier.value,
            "confidence": scraped.source_tier.trust_score,
            "updated_at": date.today().isoformat(),
        }

    @staticmethod
    def _get_provenance_tier(product: dict[str, Any], field_path: str) -> int | None:
        """Return the tier recorded in provenance for *field_path*, or ``None``."""
        provenance = _get_nested(product, "meta.provenance")
        if not isinstance(provenance, dict):
            return None
        entry = provenance.get(field_path)
        if isinstance(entry, dict):
            return entry.get("tier")
        return None

    def _record_provenance(
        self,
        product: dict[str, Any],
        field_path: str,
        scraped: ScrapedProduct,
    ) -> None:
        """Write a provenance record for *field_path* into ``meta.provenance``."""
        meta = product.setdefault("meta", {})
        prov = meta.setdefault("provenance", {})
        prov[field_path] = self._build_provenance(scraped)

    # -- company URL fallback -----------------------------------------------

    @staticmethod
    def _build_company_url(scraped: ScrapedProduct) -> str:
        """Build ``company.url`` with fallback: website > wikipedia > bing search."""
        if scraped.company_website:
            return scraped.company_website
        if scraped.company_wikipedia_url:
            return scraped.company_wikipedia_url
        company_name = scraped.company_name or scraped.name
        return f"https://www.bing.com/search?q={quote_plus(company_name)}+AI"

    # -- sources array ------------------------------------------------------

    @staticmethod
    def _append_source(product: dict[str, Any], scraped: ScrapedProduct) -> None:
        """Append to the ``sources`` array if the URL is not already present."""
        sources: list[dict[str, str]] = product.setdefault("sources", [])
        url = scraped.source_url
        if not url:
            return
        existing_urls = {s.get("url") for s in sources}
        if url not in existing_urls:
            sources.append(
                {
                    "url": url,
                    "source_name": scraped.source,
                    "scraped_at": date.today().isoformat(),
                }
            )

    # -- provenance initialization (create_new) -----------------------------

    def _collect_paths(
        self,
        data: Any,
        prefix: str,
        provenance: dict[str, Any],
        entry: dict[str, Any],
    ) -> None:
        """Recursively collect all leaf paths from *data* and populate *provenance*.

        Skips meta-level keys (``meta``, ``sources``, ``slug``) that are not
        sourced from the scraper.
        """
        skip_keys = {"meta", "sources", "slug"}
        if isinstance(data, dict):
            for key, value in data.items():
                if not prefix and key in skip_keys:
                    continue
                path = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict) and not self._is_leaf_dict(path):
                    self._collect_paths(value, path, provenance, entry)
                elif value is not None and value != "" and value != []:
                    provenance[path] = dict(entry)

    @staticmethod
    def _is_leaf_dict(path: str) -> bool:
        """Return ``True`` if *path* points to a dict that should be treated as a leaf.

        Key-people items, hiring positions, and pricing are stored as dicts but
        represent a single logical value for provenance purposes.
        """
        # These paths hold compound objects that we track as a whole.
        leaf_parents = {
            "pricing",
            "company.funding",
            "company.headquarters",
            "company.social",
        }
        return path in leaf_parents

    # -- disk I/O -----------------------------------------------------------

    @staticmethod
    def _write(filepath: Any, product: dict[str, Any]) -> None:
        """Write *product* dict to *filepath* as pretty-printed JSON."""
        filepath.write_text(
            json.dumps(product, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Backwards compatibility
# ---------------------------------------------------------------------------

Merger = TieredMerger  # Deprecated: use TieredMerger
