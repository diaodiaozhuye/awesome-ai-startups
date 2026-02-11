"""Non-destructive merger: merge scraped data into existing JSON without overwriting hand-maintained fields."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from scrapers.base import ScrapedCompany
from scrapers.config import COMPANIES_DIR
from scrapers.utils import slugify


class Merger:
    """Merge scraped company data into existing JSON files non-destructively.

    Strategy:
    - Only fill in fields that are currently null/empty in the existing file
    - Never overwrite hand-maintained data
    - Always update meta.last_updated and append to meta.sources
    """

    def merge_update(self, slug: str, scraped: ScrapedCompany) -> dict[str, Any]:
        """Merge scraped data into an existing company JSON.

        Returns the merged dict (also writes to disk).
        """
        filepath = COMPANIES_DIR / f"{slug}.json"
        existing = json.loads(filepath.read_text(encoding="utf-8"))

        merged = self._merge_fields(existing, scraped)

        # Update metadata
        meta = merged.setdefault("meta", {})
        meta["last_updated"] = date.today().isoformat()
        if scraped.source_url:
            sources = meta.setdefault("sources", [])
            if scraped.source_url not in sources:
                sources.append(scraped.source_url)

        filepath.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return merged

    def create_new(self, scraped: ScrapedCompany) -> dict[str, Any]:
        """Create a new company JSON file from scraped data.

        Returns the created dict.
        """
        slug = slugify(scraped.name)
        today = date.today().isoformat()

        company: dict[str, Any] = {
            "slug": slug,
            "name": scraped.name,
            "description": scraped.description or f"{scraped.name} is an AI company.",
            "website": scraped.website or "",
            "category": scraped.category or "ai-other",
            "founded_year": scraped.founded_year or date.today().year,
            "headquarters": {
                "city": scraped.headquarters_city or "Unknown",
                "country": scraped.headquarters_country or "Unknown",
            },
            "meta": {
                "added_date": today,
                "last_updated": today,
                "sources": [scraped.source_url] if scraped.source_url else [],
                "data_quality_score": 0.4,
            },
        }

        if scraped.headquarters_country_code:
            company["headquarters"]["country_code"] = scraped.headquarters_country_code

        if scraped.tags:
            company["tags"] = list(scraped.tags)

        if scraped.total_raised_usd:
            company["funding"] = {"total_raised_usd": scraped.total_raised_usd}
            if scraped.last_round:
                company["funding"]["last_round"] = scraped.last_round

        if scraped.github_url:
            company.setdefault("social", {})["github"] = scraped.github_url
        if scraped.twitter:
            company.setdefault("social", {})["twitter"] = scraped.twitter
        if scraped.linkedin_url:
            company.setdefault("social", {})["linkedin"] = scraped.linkedin_url

        if scraped.open_source is not None:
            company["open_source"] = scraped.open_source

        company["status"] = "active"

        filepath = COMPANIES_DIR / f"{slug}.json"
        filepath.write_text(
            json.dumps(company, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return company

    @staticmethod
    def _merge_fields(
        existing: dict[str, Any], scraped: ScrapedCompany
    ) -> dict[str, Any]:
        """Fill in empty fields from scraped data without overwriting existing values."""
        result = existing.copy()

        # Simple fields: only set if existing is empty/null
        field_map = {
            "description": scraped.description,
            "category": scraped.category,
            "founded_year": scraped.founded_year,
            "open_source": scraped.open_source,
        }

        for key, value in field_map.items():
            if value is not None and not result.get(key):
                result[key] = value

        # Website: only if missing
        if scraped.website and not result.get("website"):
            result["website"] = scraped.website

        # Headquarters: fill sub-fields
        hq = result.setdefault("headquarters", {})
        if scraped.headquarters_city and not hq.get("city"):
            hq["city"] = scraped.headquarters_city
        if scraped.headquarters_country and not hq.get("country"):
            hq["country"] = scraped.headquarters_country
        if scraped.headquarters_country_code and not hq.get("country_code"):
            hq["country_code"] = scraped.headquarters_country_code

        # Social: fill sub-fields
        if scraped.github_url or scraped.twitter or scraped.linkedin_url:
            social = result.setdefault("social", {})
            if scraped.github_url and not social.get("github"):
                social["github"] = scraped.github_url
            if scraped.twitter and not social.get("twitter"):
                social["twitter"] = scraped.twitter
            if scraped.linkedin_url and not social.get("linkedin"):
                social["linkedin"] = scraped.linkedin_url

        # Tags: append new unique tags
        if scraped.tags:
            existing_tags = set(result.get("tags", []))
            new_tags = [t for t in scraped.tags if t not in existing_tags]
            if new_tags:
                result["tags"] = list(existing_tags | set(new_tags))

        return result
