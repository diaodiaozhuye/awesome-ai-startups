"""Deduplicate companies by domain and fuzzy name matching."""

from __future__ import annotations

import json
from dataclasses import dataclass

from scrapers.base import ScrapedCompany
from scrapers.config import COMPANIES_DIR
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


# Similarity threshold for considering two names as the same company
NAME_SIMILARITY_THRESHOLD = 0.85


@dataclass
class DeduplicationResult:
    """Result of deduplication: split into new and existing companies."""

    new_companies: list[ScrapedCompany]
    updates_for_existing: list[
        tuple[str, ScrapedCompany]
    ]  # (existing_slug, scraped_data)


class Deduplicator:
    """Deduplicate scraped companies against the existing data directory."""

    def __init__(self) -> None:
        self._existing_domains: dict[str, str] = {}  # domain -> slug
        self._existing_names: dict[str, str] = {}  # lowercase name -> slug
        self._load_existing()

    def _load_existing(self) -> None:
        """Load domains and names from existing company JSON files."""
        if not COMPANIES_DIR.exists():
            return

        for filepath in COMPANIES_DIR.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                slug = data.get("slug", filepath.stem)
                name = data.get("name", "")

                if name:
                    self._existing_names[name.lower()] = slug

                website = data.get("website", "")
                if website:
                    domain = extract_domain(website)
                    if domain:
                        self._existing_domains[domain] = slug
            except (json.JSONDecodeError, KeyError):
                continue

    def deduplicate(self, companies: list[ScrapedCompany]) -> DeduplicationResult:
        """Split scraped companies into new ones and updates for existing ones."""
        new: list[ScrapedCompany] = []
        updates: list[tuple[str, ScrapedCompany]] = []

        for company in companies:
            existing_slug = self._find_existing(company)
            if existing_slug:
                updates.append((existing_slug, company))
            else:
                new.append(company)

        return DeduplicationResult(new_companies=new, updates_for_existing=updates)

    def _find_existing(self, company: ScrapedCompany) -> str | None:
        """Check if a scraped company matches any existing entry."""
        # 1. Match by domain
        if company.website:
            domain = extract_domain(company.website)
            if domain and domain in self._existing_domains:
                return self._existing_domains[domain]

        # 2. Match by exact name
        name_lower = company.name.lower()
        if name_lower in self._existing_names:
            return self._existing_names[name_lower]

        # 3. Match by fuzzy name
        for existing_name, slug in self._existing_names.items():
            if lev_ratio(name_lower, existing_name) >= NAME_SIMILARITY_THRESHOLD:
                return slug

        # 4. Match by slug
        candidate_slug = slugify(company.name)
        if (COMPANIES_DIR / f"{candidate_slug}.json").exists():
            return candidate_slug

        return None
