"""Deduplicate products by domain and fuzzy name matching."""

from __future__ import annotations

import json
from dataclasses import dataclass

from scrapers.base import ScrapedProduct
from scrapers.config import PRODUCTS_DIR
from scrapers.utils import extract_domain, slugify

try:
    from Levenshtein import ratio as lev_ratio
except ImportError:

    def lev_ratio(a: str, b: str) -> float:
        """Fallback: simple ratio based on common prefix length."""
        if not a or not b:
            return 0.0
        common = sum(1 for ca, cb in zip(a, b) if ca == cb)
        return (2.0 * common) / (len(a) + len(b))


# Similarity threshold for considering two names as the same product
NAME_SIMILARITY_THRESHOLD = 0.85


@dataclass
class DeduplicationResult:
    """Result of deduplication: split into new and existing products."""

    new_products: list[ScrapedProduct]
    updates_for_existing: list[
        tuple[str, ScrapedProduct]
    ]  # (existing_slug, scraped_data)


class Deduplicator:
    """Deduplicate scraped products against the existing data directory."""

    def __init__(self) -> None:
        self._existing_domains: dict[str, str] = {}  # domain -> slug
        self._existing_names: dict[str, str] = {}  # lowercase name -> slug
        self._load_existing()

    def _load_existing(self) -> None:
        """Load domains and names from existing product JSON files."""
        if not PRODUCTS_DIR.exists():
            return

        for filepath in PRODUCTS_DIR.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                slug = data.get("slug", filepath.stem)
                name = data.get("name", "")

                if name:
                    self._existing_names[name.lower()] = slug

                # Match on product_url domain
                product_url = data.get("product_url", "")
                if product_url:
                    domain = extract_domain(product_url)
                    if domain:
                        self._existing_domains[domain] = slug

                # Also match on company.website domain
                company = data.get("company", {})
                company_website = company.get("website", "") if company else ""
                if company_website:
                    domain = extract_domain(company_website)
                    if domain:
                        self._existing_domains[domain] = slug
            except (json.JSONDecodeError, KeyError):
                continue

    def deduplicate(self, products: list[ScrapedProduct]) -> DeduplicationResult:
        """Split scraped products into new ones and updates for existing ones."""
        new: list[ScrapedProduct] = []
        updates: list[tuple[str, ScrapedProduct]] = []

        for product in products:
            existing_slug = self._find_existing(product)
            if existing_slug:
                updates.append((existing_slug, product))
            else:
                new.append(product)

        return DeduplicationResult(new_products=new, updates_for_existing=updates)

    def _find_existing(self, product: ScrapedProduct) -> str | None:
        """Check if a scraped product matches any existing entry."""
        # 1. Match by product_url domain
        if product.product_url:
            domain = extract_domain(product.product_url)
            if domain and domain in self._existing_domains:
                return self._existing_domains[domain]

        # 2. Match by company_website domain
        if product.company_website:
            domain = extract_domain(product.company_website)
            if domain and domain in self._existing_domains:
                return self._existing_domains[domain]

        # 3. Match by exact name
        name_lower = product.name.lower()
        if name_lower in self._existing_names:
            return self._existing_names[name_lower]

        # 4. Match by fuzzy name
        for existing_name, slug in self._existing_names.items():
            if lev_ratio(name_lower, existing_name) >= NAME_SIMILARITY_THRESHOLD:
                return slug

        # 5. Match by slug
        candidate_slug = slugify(product.name)
        if (PRODUCTS_DIR / f"{candidate_slug}.json").exists():
            return candidate_slug

        return None
