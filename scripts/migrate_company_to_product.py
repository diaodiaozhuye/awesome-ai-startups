#!/usr/bin/env python3
"""Migrate company JSON files to product-centric format.

Reads data/companies/*.json and creates data/products/*.json.
Garbage data is cleaned or archived.

Usage:
    python scripts/migrate_company_to_product.py
    python scripts/migrate_company_to_product.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
COMPANIES_DIR = REPO_ROOT / "data" / "companies"
PRODUCTS_DIR = REPO_ROOT / "data" / "products"
ARCHIVE_DIR = REPO_ROOT / "data" / "archive"

# ---------------------------------------------------------------------------
# Category mapping: old company category -> new product category
# ---------------------------------------------------------------------------
CATEGORY_MAP: dict[str, str] = {
    "llm-foundation-model": "ai-model",
    "ai-coding": "ai-dev-tool",
    "ai-image-video": "ai-model",
    "ai-audio-speech": "ai-model",
    "ai-search": "ai-search",
    "ai-robotics": "ai-hardware",
    "ai-infrastructure": "ai-infrastructure",
    "ai-data-analytics": "ai-data",
    "ai-assistant": "ai-app",
    "ai-enterprise": "ai-app",
    "autonomous-vehicles": "ai-hardware",
    "ai-security-defense": "ai-security",
    "ai-healthcare": "ai-app",
    "ai-education": "ai-app",
    "ai-finance": "ai-app",
    "ai-gaming": "ai-app",
    "ai-other": "ai-app",  # default fallback
}

# ---------------------------------------------------------------------------
# Sub-category best-guess mapping
# ---------------------------------------------------------------------------
SUB_CATEGORY_MAP: dict[str, str | None] = {
    "llm-foundation-model": "text-generation",
    "ai-coding": "coding-assistant",
    "ai-image-video": "image-generation",
    "ai-audio-speech": "audio-speech",
    "ai-search": "web-search",
    "ai-robotics": "robot",
    "ai-infrastructure": "compute-platform",
    "ai-data-analytics": "data-pipeline",
    "ai-assistant": "personal-assistant",
    "ai-enterprise": "workflow-automation",
    "autonomous-vehicles": "autonomous-vehicle",
    "ai-security-defense": "ai-safety",
    "ai-healthcare": "healthcare-medical",
    "ai-education": "education-tutoring",
    "ai-finance": "finance-accounting",
    "ai-gaming": None,  # no good sub_category
    "ai-other": None,
}

# ---------------------------------------------------------------------------
# Product type inference from old category
# ---------------------------------------------------------------------------
PRODUCT_TYPE_MAP: dict[str, str] = {
    "llm-foundation-model": "llm",
    "ai-coding": "dev-tool",
    "ai-image-video": "llm",
    "ai-audio-speech": "llm",
    "ai-search": "app",
    "ai-robotics": "hardware",
    "ai-infrastructure": "api-service",
    "ai-data-analytics": "dev-tool",
    "ai-assistant": "app",
    "ai-enterprise": "app",
    "autonomous-vehicles": "hardware",
    "ai-security-defense": "app",
    "ai-healthcare": "app",
    "ai-education": "app",
    "ai-finance": "app",
    "ai-gaming": "app",
    "ai-other": "other",
}

# ---------------------------------------------------------------------------
# Slugs to archive (clearly not AI products / ghost entries from scrapers)
# ---------------------------------------------------------------------------
ARCHIVE_SLUGS: frozenset[str] = frozenset(
    {
        # Ghost / placeholder entries
        "stealth-startup",
        "stealth-ai-startup",
        # Consulting / outsourcing / staffing firms
        "avance-consulting",
        "praxent",
        "enableit",
        "azumo",
        # Logistics / industrial / non-tech
        "centerline-logistics-corporation",
        "dixon-group-europe-ltd-middle-east",
        "grassroots-carbon",
        "prana-tree",
        "crossing-hurdles",
        # IT services with zero AI data
        "fionics",
        "leotech",
        "netic",
        "cymertek-corporation",
        # Well-known non-AI-product companies scraped from job boards
        "tinder",
        "handshake",
        "netflix",
        "honeywell",
        "linkedin",
        "point72",
        "ecosave",
        "energize-group",
        "erg",
        "cis",
        "giga",
        "middesk",
        # Hacking resources repo (not a product)
        "art-of-hacking",
    }
)

# ---------------------------------------------------------------------------
# Garbage patterns found in scraped text fields
# ---------------------------------------------------------------------------
_GARBAGE_PATTERN: re.Pattern[str] = re.compile(
    r"("
    r"\d+\s*days?\s*ago"
    r"|Actively\s*Hiring"
    r"|Apply\s*Now"
    r"|Click"
    r"|\d+\s*hours?\s*ago"
    r"|Posted\s*\d+"
    r"|Easy\s*Apply"
    r"|\d+\s*weeks?\s*ago"
    r"|\d+\s*months?\s*ago"
    r"|\+\d+\s*benefits?"
    r")",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def clean_text(text: str | None) -> str | None:
    """Remove garbage text patterns (job-board artifacts) from a string."""
    if not text:
        return None
    cleaned = _GARBAGE_PATTERN.sub("", text).strip()
    # Also strip leading/trailing punctuation that becomes orphaned
    cleaned = cleaned.strip(",;:- \n\t")
    return cleaned if cleaned else None


def clean_founded_year(year: int | None) -> int | None:
    """Return None if year looks like a default/garbage value."""
    if year is None:
        return None
    current_year = date.today().year
    # Old scrapers defaulted to the current year when unknown
    if year == current_year:
        return None
    if year < 1900 or year > current_year:
        return None
    return year


def build_company_url(
    website: str | None,
    social: dict[str, str] | None,
    name: str,
) -> str:
    """Build company.url with a fallback chain: website -> social -> Bing search."""
    if website and website.strip():
        return website.strip()
    # Try any useful URL from social links
    if social:
        for key in ("crunchbase", "linkedin", "github"):
            val = social.get(key)
            if val and val.strip():
                return val.strip()
    # Last-resort: Bing search URL
    return f"https://www.bing.com/search?q={quote_plus(name + ' AI')}"


def _is_placeholder_description(desc: str, name: str) -> bool:
    """Return True if the description is a useless placeholder."""
    normalized = desc.strip().rstrip(".")
    return normalized == f"{name} is an AI company"


def _map_status(old_status: str) -> str:
    """Map old company status to new product status enum."""
    mapping: dict[str, str] = {
        "active": "active",
        "acquired": "active",  # product may still be active
        "shut-down": "discontinued",
        "ipo": "active",
    }
    return mapping.get(old_status, "active")


# ---------------------------------------------------------------------------
# Core migration logic
# ---------------------------------------------------------------------------


def migrate_company(filepath: Path) -> dict[str, object] | None:
    """Convert a single company JSON to the new product JSON format.

    Returns the product dict, or ``None`` if the entry should be archived.
    """
    data: dict[str, object] = json.loads(filepath.read_text(encoding="utf-8"))
    slug: str = str(data.get("slug", filepath.stem))

    # --- Archive garbage entries ------------------------------------------------
    if slug in ARCHIVE_SLUGS:
        return None

    # Skip entries with a boilerplate description *and* no website at all
    desc_raw: str = str(data.get("description", ""))
    name: str = str(data.get("name", slug))
    website_raw: str = str(data.get("website", "")).strip()
    if _is_placeholder_description(desc_raw, name) and not website_raw:
        return None

    # --- Pull nested objects from old format -----------------------------------
    old_cat: str = str(data.get("category", "ai-other"))
    today: str = date.today().isoformat()

    hq: dict[str, str] = dict(data.get("headquarters", {}))  # type: ignore[arg-type]
    social: dict[str, str] = dict(data.get("social", {}))  # type: ignore[arg-type]
    funding: dict[str, object] = dict(data.get("funding", {}))  # type: ignore[arg-type]
    team: dict[str, object] = dict(data.get("team", {}))  # type: ignore[arg-type]
    meta: dict[str, object] = dict(data.get("meta", {}))  # type: ignore[arg-type]

    website: str | None = website_raw or None

    # --- Determine product URL and product name --------------------------------
    products_list: list[dict[str, str]] = list(data.get("products", []))  # type: ignore[arg-type]
    product_url: str | None = website  # default to company website
    product_name: str = name
    if products_list and products_list[0].get("url"):
        product_url = products_list[0]["url"]
        product_name = products_list[0].get("name", name)

    if not product_url:
        product_url = build_company_url(None, social, name)

    # --- Build top-level product dict ------------------------------------------
    description: str = desc_raw if desc_raw else f"{product_name} is an AI product."

    product: dict[str, object] = {
        "slug": slug,
        "name": product_name,
        "product_url": product_url,
        "description": description,
        "product_type": PRODUCT_TYPE_MAP.get(old_cat, "other"),
        "category": CATEGORY_MAP.get(old_cat, "ai-app"),
        "status": _map_status(str(data.get("status", "active"))),
    }

    # Optional i18n fields
    if data.get("name_zh"):
        product["name_zh"] = data["name_zh"]
    if data.get("description_zh"):
        product["description_zh"] = data["description_zh"]

    # Sub-category
    sub_cat: str | None = SUB_CATEGORY_MAP.get(old_cat)
    if sub_cat:
        product["sub_category"] = sub_cat

    # Tags (filter out scraper-internal tags like "linkedin")
    tags: list[str] = list(data.get("tags", []))  # type: ignore[arg-type]
    clean_tags = [t for t in tags if t not in {"linkedin", "github-scraper"}]
    if clean_tags:
        product["tags"] = clean_tags

    # Open source flag
    if data.get("open_source") is not None:
        product["open_source"] = data["open_source"]

    # Repository URL (from social.github)
    if social.get("github"):
        product["repository_url"] = social["github"]

    # --- Embedded company object -----------------------------------------------
    company: dict[str, object] = {
        "name": name,
        "url": build_company_url(website, social, name),
    }
    if website:
        company["website"] = website
    if data.get("name_zh"):
        company["name_zh"] = data["name_zh"]

    cleaned_year = clean_founded_year(
        int(data["founded_year"]) if data.get("founded_year") is not None else None,
    )
    if cleaned_year:
        company["founded_year"] = cleaned_year

    # Clean headquarters of garbage text
    cleaned_city = clean_text(hq.get("city"))
    cleaned_country = clean_text(hq.get("country"))
    if cleaned_city or cleaned_country:
        headquarters: dict[str, str] = {}
        if cleaned_city:
            headquarters["city"] = cleaned_city
        state = hq.get("state")
        if state:
            headquarters["state"] = state
        if cleaned_country and cleaned_country != "Unknown":
            headquarters["country"] = cleaned_country
        country_code = hq.get("country_code")
        if country_code:
            headquarters["country_code"] = country_code
        if headquarters:
            company["headquarters"] = headquarters

    # Funding
    if funding:
        company["funding"] = funding

    # Employee count
    employee_range = team.get("employee_count_range")
    if employee_range:
        company["employee_count_range"] = employee_range

    # Social links (company-level)
    company_social: dict[str, str] = {}
    for key in ("linkedin", "crunchbase", "twitter", "github"):
        val = social.get(key)
        if val and val.strip():
            company_social[key] = val.strip()
    if company_social:
        company["social"] = company_social

    product["company"] = company

    # --- Key people (migrated from team.founders) ------------------------------
    founders: list[dict[str, str]] = list(team.get("founders", []))  # type: ignore[arg-type]
    if founders:
        key_people: list[dict[str, object]] = []
        for f in founders:
            person: dict[str, object] = {"name": f["name"]}
            if f.get("title"):
                person["title"] = f["title"]
            person["is_founder"] = True
            if f.get("linkedin"):
                person["profile_url"] = f["linkedin"]
            key_people.append(person)
        product["key_people"] = key_people

    # --- Sources (migrated from meta.sources) ----------------------------------
    old_sources: list[str] = list(meta.get("sources", []))  # type: ignore[arg-type]
    sources: list[dict[str, str]] = []
    for src in old_sources:
        if isinstance(src, str) and src.strip():
            sources.append(
                {
                    "url": src.strip(),
                    "source_name": "migration",
                    "scraped_at": today,
                }
            )
    if sources:
        product["sources"] = sources

    # --- Meta ------------------------------------------------------------------
    product["meta"] = {
        "added_date": str(meta.get("added_date", today)),
        "last_updated": today,
        "data_quality_score": 0.0,  # Will be recalculated by QualityScorer
        "needs_review": True,  # All migrated data needs manual review
    }

    return product


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the migration."""
    parser = argparse.ArgumentParser(
        description="Migrate company JSONs to product format."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without writing files.",
    )
    args = parser.parse_args()

    if not COMPANIES_DIR.exists():
        print(f"ERROR: Companies directory not found: {COMPANIES_DIR}", file=sys.stderr)
        sys.exit(1)

    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    company_files = sorted(COMPANIES_DIR.glob("*.json"))

    migrated = 0
    archived = 0
    errors = 0

    for filepath in company_files:
        try:
            product = migrate_company(filepath)

            if product is None:
                # Archive the file
                if args.dry_run:
                    print(f"  [DRY-RUN] ARCHIVE: {filepath.stem}")
                else:
                    archive_path = ARCHIVE_DIR / filepath.name
                    archive_path.write_text(
                        filepath.read_text(encoding="utf-8"),
                        encoding="utf-8",
                    )
                    print(f"  ARCHIVED: {filepath.stem}")
                archived += 1
                continue

            # Write product JSON
            if args.dry_run:
                print(f"  [DRY-RUN] MIGRATE: {filepath.stem}")
            else:
                out_path = PRODUCTS_DIR / f"{product['slug']}.json"
                out_path.write_text(
                    json.dumps(product, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                print(f"  MIGRATED: {filepath.stem}")
            migrated += 1

        except Exception as e:
            errors += 1
            print(f"  ERROR: {filepath.stem}: {e}", file=sys.stderr)

    print("\nMigration complete:")
    print(f"  Migrated:  {migrated}")
    print(f"  Archived:  {archived}")
    print(f"  Errors:    {errors}")
    print(f"  Total:     {len(company_files)}")

    if args.dry_run:
        print("\n  (dry-run mode — no files were written)")


if __name__ == "__main__":
    main()
