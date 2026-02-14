"""Compute weighted data quality score for AI product JSON files."""

from __future__ import annotations

from typing import Any

# Field weights: more important fields get higher weight
_FIELD_WEIGHTS: dict[str, float] = {
    # Core identity (highest weight)
    "name": 3.0,
    "product_url": 3.0,
    "description": 3.0,
    "product_type": 2.0,
    "category": 2.0,
    "sub_category": 1.5,
    "icon_url": 1.0,
    # Company info
    "company.name": 2.0,
    "company.url": 2.0,
    "company.website": 1.5,
    "company.founded_year": 1.0,
    "company.headquarters": 1.0,
    "company.description": 0.5,
    "company.funding": 0.5,
    # Tech
    "architecture": 1.0,
    "modalities": 1.0,
    "platforms": 1.0,
    "api_available": 0.5,
    # Open source
    "open_source": 0.5,
    "repository_url": 0.5,
    # Pricing
    "pricing": 1.0,
    # Community
    "tags": 1.0,
    "keywords": 1.0,
    # People
    "key_people": 0.5,
    # Sources
    "sources": 1.0,
    # Status
    "status": 1.0,
    "description_zh": 0.5,
}


class QualityScorer:
    """Compute weighted data quality score for product JSON data."""

    def score(self, product: dict[str, Any]) -> float:
        """Compute quality score (0.0 to 1.0) based on field completeness."""
        total_weight = sum(_FIELD_WEIGHTS.values())
        earned_weight = 0.0

        for field_path, weight in _FIELD_WEIGHTS.items():
            if self._field_has_value(product, field_path):
                earned_weight += weight

        return round(earned_weight / total_weight, 2)

    @staticmethod
    def _field_has_value(product: dict[str, Any], field_path: str) -> bool:
        """Check if a nested field has a non-empty value."""
        parts = field_path.split(".")
        current: Any = product
        for part in parts:
            if not isinstance(current, dict):
                return False
            current = current.get(part)
            if current is None:
                return False
        # Check for empty strings, empty lists, empty dicts
        if isinstance(current, str) and not current.strip():
            return False
        return not (isinstance(current, (list, dict)) and not current)
