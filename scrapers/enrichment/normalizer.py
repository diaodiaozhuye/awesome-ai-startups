"""Normalize scraped product data: names, URLs, countries, categories."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import date

from scrapers.base import ScrapedProduct
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
    """Normalize ScrapedProduct fields to standard formats."""

    def __init__(self) -> None:
        self._valid_categories: set[str] = set()
        if CATEGORIES_FILE.exists():
            data = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
            self._valid_categories = {c["id"] for c in data.get("categories", [])}

    def normalize(self, product: ScrapedProduct) -> ScrapedProduct:
        """Normalize all fields of a ScrapedProduct."""
        return replace(
            product,
            name=self._normalize_name(product.name),
            company_website=(
                normalize_url(product.company_website)
                if product.company_website
                else None
            ),
            company_headquarters_country=self._normalize_country(
                product.company_headquarters_country
            ),
            company_headquarters_country_code=self._resolve_country_code(
                product.company_headquarters_country
            ),
            category=self._normalize_category(product.category),
        )

    def compute_quality_score(self, product: ScrapedProduct) -> float:
        """Compute a data quality score (0-1) based on field completeness."""
        fields = [
            product.name,
            product.company_website,
            product.description,
            product.category,
            product.company_founded_year,
            product.company_headquarters_country,
            product.company_total_raised_usd,
            product.company_employee_count_range,
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


class PlausibilityValidator:
    """Reject implausible or garbage data before it enters the pipeline."""

    # Patterns that indicate garbage data from job scrapers
    _GARBAGE_COUNTRY_PATTERNS = re.compile(
        r"(remote|hybrid|on-site|full-time|part-time|contract|intern|"
        r"\d+k|\$|salary|experience|years|senior|junior|"
        r"apply now|click|http|www\.)",
        re.IGNORECASE,
    )

    _MIN_DESCRIPTION_LENGTH = 10
    _MAX_DESCRIPTION_LENGTH = 5000
    _MIN_FOUNDED_YEAR = 1900
    _MAX_FOUNDED_YEAR = 2035

    def validate(self, product: ScrapedProduct) -> tuple[bool, list[str]]:
        """Validate a ScrapedProduct for plausibility.

        Returns (is_valid, list_of_issues).
        """
        issues: list[str] = []

        # Check name
        if not product.name or len(product.name.strip()) < 2:
            issues.append("Name too short or empty")

        # Check description length
        if product.description:
            desc_len = len(product.description.strip())
            if desc_len < self._MIN_DESCRIPTION_LENGTH:
                issues.append(f"Description too short ({desc_len} chars)")
            if desc_len > self._MAX_DESCRIPTION_LENGTH:
                issues.append(f"Description too long ({desc_len} chars)")

        # Check founded_year is not garbage
        if product.company_founded_year is not None:
            year = product.company_founded_year
            if year < self._MIN_FOUNDED_YEAR or year > self._MAX_FOUNDED_YEAR:
                issues.append(f"Founded year {year} outside valid range")
            # Detect default current-year values from job scrapers
            if year == date.today().year:
                issues.append(f"Founded year {year} looks like default (current year)")

        # Check country is not garbage from job postings
        country = product.company_headquarters_country
        if country and self._GARBAGE_COUNTRY_PATTERNS.search(country):
            issues.append(f"Country '{country}' looks like garbage data")

        # Check URLs are valid-looking
        if product.product_url and not product.product_url.startswith(
            ("http://", "https://")
        ):
            issues.append(f"Product URL '{product.product_url}' is not a valid URL")

        if product.company_website and not product.company_website.startswith(
            ("http://", "https://")
        ):
            issues.append(
                f"Company website '{product.company_website}' is not a valid URL"
            )

        return (len(issues) == 0, issues)
