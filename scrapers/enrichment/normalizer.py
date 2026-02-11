"""Normalize scraped company data: names, URLs, countries, categories."""

from __future__ import annotations

import json
import re
from dataclasses import replace

from scrapers.base import ScrapedCompany
from scrapers.config import CATEGORIES_FILE
from scrapers.utils import normalize_url, slugify

# Common suffixes to strip for cleaner company names
_NAME_SUFFIXES = re.compile(
    r"\s*(,?\s*(Inc\.?|LLC|Ltd\.?|Corp\.?|Co\.?))\s*$", re.IGNORECASE
)

# Country name normalization map
_COUNTRY_MAP: dict[str, str] = {
    "usa": "United States",
    "us": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "gb": "United Kingdom",
    "great britain": "United Kingdom",
    "prc": "China",
    "cn": "China",
    "de": "Germany",
    "fr": "France",
    "jp": "Japan",
    "kr": "South Korea",
    "ca": "Canada",
    "au": "Australia",
    "il": "Israel",
    "sg": "Singapore",
    "in": "India",
    "se": "Sweden",
    "no": "Norway",
}

# Country to country_code
_COUNTRY_CODES: dict[str, str] = {
    "United States": "US",
    "United Kingdom": "GB",
    "China": "CN",
    "Germany": "DE",
    "France": "FR",
    "Japan": "JP",
    "South Korea": "KR",
    "Canada": "CA",
    "Australia": "AU",
    "Israel": "IL",
    "Singapore": "SG",
    "India": "IN",
    "Sweden": "SE",
    "Norway": "NO",
}


class Normalizer:
    """Normalize ScrapedCompany fields to standard formats."""

    def __init__(self) -> None:
        self._valid_categories: set[str] = set()
        if CATEGORIES_FILE.exists():
            data = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
            self._valid_categories = {c["id"] for c in data.get("categories", [])}

    def normalize(self, company: ScrapedCompany) -> ScrapedCompany:
        """Normalize all fields of a ScrapedCompany."""
        return replace(
            company,
            name=self._normalize_name(company.name),
            website=normalize_url(company.website) if company.website else None,
            headquarters_country=self._normalize_country(company.headquarters_country),
            headquarters_country_code=self._resolve_country_code(
                company.headquarters_country
            ),
            category=self._normalize_category(company.category),
        )

    def compute_quality_score(self, company: ScrapedCompany) -> float:
        """Compute a data quality score (0-1) based on field completeness."""
        fields = [
            company.name,
            company.website,
            company.description,
            company.category,
            company.founded_year,
            company.headquarters_country,
            company.total_raised_usd,
            company.employee_count_range,
        ]
        filled = sum(1 for f in fields if f is not None and f != "")
        return round(filled / len(fields), 2)

    @staticmethod
    def _normalize_name(name: str) -> str:
        name = name.strip()
        name = _NAME_SUFFIXES.sub("", name)
        return name

    @staticmethod
    def _normalize_country(country: str | None) -> str | None:
        if not country:
            return None
        normalized = _COUNTRY_MAP.get(country.lower().strip())
        return normalized or country.strip()

    @staticmethod
    def _resolve_country_code(country: str | None) -> str | None:
        if not country:
            return None
        normalized = _COUNTRY_MAP.get(country.lower().strip(), country.strip())
        return _COUNTRY_CODES.get(normalized)

    def _normalize_category(self, category: str | None) -> str | None:
        if not category:
            return None
        slug = slugify(category)
        if slug in self._valid_categories:
            return slug
        return None
