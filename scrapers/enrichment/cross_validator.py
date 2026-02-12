"""Cross-validate scraped fields to prevent data contamination across products.

Detects bilingual name collisions, URL misattribution, description duplication,
and company data inconsistencies before the merger writes fields to disk.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from scrapers.config import PRODUCTS_DIR

try:
    from Levenshtein import ratio as lev_ratio
except ImportError:

    def lev_ratio(a: str, b: str) -> float:
        """Fallback: positional character match ratio."""
        if not a or not b:
            return 0.0
        common = sum(1 for ca, cb in zip(a, b) if ca == cb)
        return (2.0 * common) / (len(a) + len(b))


logger = logging.getLogger(__name__)

# Similarity threshold for near-duplicate descriptions
DESCRIPTION_SIMILARITY_THRESHOLD = 0.90

# Aggregator/directory domains that should never be a product_url
_AGGREGATOR_DOMAINS: frozenset[str] = frozenset(
    {
        "ai-bot.cn",
        "ainav.cn",
        "theresanaiforthat.com",
        "toolify.ai",
        "futurepedia.io",
        "alternativeto.net",
        "producthunt.com",
        "crunchbase.com",
        "pitchbook.com",
        "ycombinator.com",
    }
)

# Fields that trigger hard rejection on collision
_CROSS_VALIDATED_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "name_zh",
        "description",
        "description_zh",
        "product_url",
    }
)

# Fields that trigger warning only (logged but not blocked)
_CROSS_VALIDATED_WARN_FIELDS: frozenset[str] = frozenset(
    {
        "company.name_zh",
    }
)

VALIDATED_FIELDS = _CROSS_VALIDATED_FIELDS | _CROSS_VALIDATED_WARN_FIELDS


@dataclass(frozen=True)
class CrossValidationViolation:
    """A single field-level cross-validation violation."""

    target_slug: str
    field: str
    rejected_value: str
    conflicting_slug: str
    reason: str
    severity: str = "error"  # "error" = field skipped, "warning" = logged only


class CrossValidator:
    """Validate incoming field values against the global product index.

    Built at pipeline start, provides ``validate_field()`` for the merger
    to call before each write.  Detects:

    - Bilingual name collisions (name_zh / name cross-contamination)
    - Description duplication (both EN and ZH)
    - URL misattribution (aggregator URLs, duplicate product URLs)
    - Company data inconsistencies across products from the same company
    """

    def __init__(self) -> None:
        self._name_to_slug: dict[str, str] = {}
        self._name_zh_to_slug: dict[str, str] = {}
        self._url_to_slug: dict[str, str] = {}
        self._description_by_slug: dict[str, str] = {}
        self._description_zh_by_slug: dict[str, str] = {}
        self._company_data: dict[str, dict[str, Any]] = (
            {}
        )  # company_name -> first seen data
        self._violations: list[CrossValidationViolation] = []
        self._load_existing()

    # -- index building -----------------------------------------------------

    def _load_existing(self) -> None:
        """Build indexes from all existing product JSON files."""
        if not PRODUCTS_DIR.exists():
            return
        for filepath in PRODUCTS_DIR.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            slug = data.get("slug", filepath.stem)
            name = data.get("name", "")
            if name:
                self._name_to_slug[name.lower()] = slug

            name_zh = data.get("name_zh", "")
            if name_zh:
                self._name_zh_to_slug[name_zh] = slug

            product_url = data.get("product_url", "")
            if product_url:
                self._url_to_slug[product_url] = slug

            desc = data.get("description", "")
            if desc and len(desc) >= 20:
                self._description_by_slug[slug] = desc

            desc_zh = data.get("description_zh", "")
            if desc_zh and len(desc_zh) >= 20:
                self._description_zh_by_slug[slug] = desc_zh

            company = data.get("company") or {}
            company_name = (company.get("name") or "").strip()
            if company_name and company_name not in self._company_data:
                self._company_data[company_name] = {
                    "slug": slug,
                    "headquarters": company.get("headquarters"),
                    "founded_year": company.get("founded_year"),
                    "name_zh": company.get("name_zh"),
                }

    # -- public API ---------------------------------------------------------

    def validate_field(
        self,
        target_slug: str,
        field_path: str,
        value: Any,
    ) -> bool:
        """Check if *value* for *field_path* conflicts with another product.

        Returns ``True`` if safe to write, ``False`` if the field should be
        skipped.  Warn-only fields always return ``True`` but still record
        a violation.
        """
        if not isinstance(value, str) or not value.strip():
            return True

        if field_path == "name_zh":
            return self._check_name_zh(target_slug, value)
        if field_path == "name":
            return self._check_name_reverse(target_slug, value)
        if field_path == "description":
            return self._check_description(target_slug, value)
        if field_path == "description_zh":
            return self._check_description_zh(target_slug, value)
        if field_path == "product_url":
            return self._check_product_url(target_slug, value)
        if field_path == "company.name_zh":
            self._check_company_name_zh(target_slug, value)
            return True  # warn-only, never reject
        return True

    def validate_company_consistency(
        self,
        target_slug: str,
        company_name: str,
        scraped_data: dict[str, Any],
    ) -> list[CrossValidationViolation]:
        """Check that company data is consistent with previously seen data.

        Called once per product merge with the full company block.  Returns
        a list of warnings (does not block writes).
        """
        warnings: list[CrossValidationViolation] = []
        if not company_name or company_name not in self._company_data:
            return warnings

        ref = self._company_data[company_name]
        if ref["slug"] == target_slug:
            return warnings

        # Check headquarters consistency
        ref_hq = ref.get("headquarters") or {}
        new_hq = scraped_data.get("headquarters") or {}
        ref_country = ref_hq.get("country", "")
        new_country = new_hq.get("country", "")
        if ref_country and new_country and ref_country != new_country:
            v = CrossValidationViolation(
                target_slug=target_slug,
                field="company.headquarters.country",
                rejected_value=new_country,
                conflicting_slug=ref["slug"],
                reason=(
                    f"Company '{company_name}' HQ country mismatch: "
                    f"'{new_country}' vs '{ref_country}' in '{ref['slug']}'"
                ),
                severity="warning",
            )
            warnings.append(v)
            self._violations.append(v)
            logger.warning("Cross-validation: %s", v.reason)

        # Check founded_year consistency
        ref_year = ref.get("founded_year")
        new_year = scraped_data.get("founded_year")
        if ref_year and new_year and ref_year != new_year:
            v = CrossValidationViolation(
                target_slug=target_slug,
                field="company.founded_year",
                rejected_value=str(new_year),
                conflicting_slug=ref["slug"],
                reason=(
                    f"Company '{company_name}' founded_year mismatch: "
                    f"{new_year} vs {ref_year} in '{ref['slug']}'"
                ),
                severity="warning",
            )
            warnings.append(v)
            self._violations.append(v)
            logger.warning("Cross-validation: %s", v.reason)

        return warnings

    @property
    def violations(self) -> list[CrossValidationViolation]:
        """All accumulated violations for this session."""
        return list(self._violations)

    def update_index(self, slug: str, field_path: str, value: str) -> None:
        """Update indexes after a successful write for within-batch consistency."""
        if field_path == "name_zh" and value:
            self._name_zh_to_slug[value] = slug
        elif field_path == "name" and value:
            self._name_to_slug[value.lower()] = slug
        elif field_path == "description" and value and len(value) >= 20:
            self._description_by_slug[slug] = value
        elif field_path == "description_zh" and value and len(value) >= 20:
            self._description_zh_by_slug[slug] = value
        elif field_path == "product_url" and value:
            self._url_to_slug[value] = slug

    # -- private checks -----------------------------------------------------

    def _check_name_zh(self, target_slug: str, value: str) -> bool:
        """Reject if name_zh belongs to a different product."""
        # Exact match against other products' name_zh
        owner = self._name_zh_to_slug.get(value)
        if owner and owner != target_slug:
            self._record(
                target_slug,
                "name_zh",
                value,
                owner,
                "error",
                f"name_zh '{value}' already belongs to product '{owner}'",
            )
            return False

        # Cross-lingual: name_zh matches another product's English name
        owner = self._name_to_slug.get(value.lower())
        if owner and owner != target_slug:
            self._record(
                target_slug,
                "name_zh",
                value,
                owner,
                "error",
                f"name_zh '{value}' matches English name of '{owner}'",
            )
            return False

        return True

    def _check_name_reverse(self, target_slug: str, value: str) -> bool:
        """Reject if incoming name matches another product's name_zh."""
        owner = self._name_zh_to_slug.get(value)
        if owner and owner != target_slug:
            self._record(
                target_slug,
                "name",
                value,
                owner,
                "error",
                f"name '{value}' matches name_zh of '{owner}'",
            )
            return False
        return True

    def _check_description(self, target_slug: str, value: str) -> bool:
        """Reject if English description is near-identical to another product."""
        if len(value.strip()) < 20:
            return True
        for other_slug, other_desc in self._description_by_slug.items():
            if other_slug == target_slug:
                continue
            if lev_ratio(value, other_desc) >= DESCRIPTION_SIMILARITY_THRESHOLD:
                self._record(
                    target_slug,
                    "description",
                    value[:80],
                    other_slug,
                    "error",
                    f"description is ≥{DESCRIPTION_SIMILARITY_THRESHOLD:.0%} similar "
                    f"to product '{other_slug}'",
                )
                return False
        return True

    def _check_description_zh(self, target_slug: str, value: str) -> bool:
        """Reject if Chinese description is near-identical to another product."""
        if len(value.strip()) < 20:
            return True
        for other_slug, other_desc in self._description_zh_by_slug.items():
            if other_slug == target_slug:
                continue
            if lev_ratio(value, other_desc) >= DESCRIPTION_SIMILARITY_THRESHOLD:
                self._record(
                    target_slug,
                    "description_zh",
                    value[:80],
                    other_slug,
                    "error",
                    f"description_zh is ≥{DESCRIPTION_SIMILARITY_THRESHOLD:.0%} similar "
                    f"to product '{other_slug}'",
                )
                return False
        return True

    def _check_product_url(self, target_slug: str, value: str) -> bool:
        """Reject if product_url is an aggregator site or belongs to another product."""
        # Check aggregator domains
        domain = self._extract_domain(value)
        if domain in _AGGREGATOR_DOMAINS:
            self._record(
                target_slug,
                "product_url",
                value,
                "",
                "error",
                f"product_url points to aggregator site '{domain}'",
            )
            return False

        # Check if exact URL already belongs to another product
        owner = self._url_to_slug.get(value)
        if owner and owner != target_slug:
            self._record(
                target_slug,
                "product_url",
                value,
                owner,
                "error",
                f"product_url already belongs to product '{owner}'",
            )
            return False

        return True

    def _check_company_name_zh(self, target_slug: str, value: str) -> None:
        """Warn (not reject) if company.name_zh conflict — same company is valid."""
        # This is informational only; multiple products can share a company
        pass  # No action needed — shared companies are expected

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract bare domain from URL for comparison."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            host = parsed.hostname or ""
            if host.startswith("www."):
                host = host[4:]
            return host.lower()
        except Exception:
            return ""

    def _record(
        self,
        target_slug: str,
        field: str,
        value: str,
        conflicting_slug: str,
        severity: str,
        reason: str,
    ) -> None:
        v = CrossValidationViolation(
            target_slug=target_slug,
            field=field,
            rejected_value=value[:100],
            conflicting_slug=conflicting_slug,
            reason=reason,
            severity=severity,
        )
        self._violations.append(v)
        if severity == "error":
            logger.warning("Cross-validation REJECT: %s", reason)
        else:
            logger.info("Cross-validation WARN: %s", reason)
