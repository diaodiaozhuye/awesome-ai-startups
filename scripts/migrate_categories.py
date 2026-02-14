#!/usr/bin/env python3
"""Phase 2: Migrate product categories (10 → 11) and tags (flat → dimensional).

Usage:
    python scripts/migrate_categories.py          # Execute migration
    python scripts/migrate_categories.py --dry-run # Preview changes
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = REPO_ROOT / "data" / "products"
TAGS_FILE = REPO_ROOT / "data" / "tags.json"

# ── Category mapping: old 10 → new 11 ──────────────────────────────────────

# Default mapping (1:1 renames)
_CATEGORY_MAP: dict[str, str] = {
    "ai-infrastructure": "ai-infrastructure",
    "ai-dev-tool": "ai-dev-platform",
    "ai-data": "ai-data-platform",
    "ai-search": "ai-search-retrieval",
    "ai-security": "ai-security-governance",
    "ai-science": "ai-science-research",
    "ai-hardware": "ai-hardware",
}

# ai-model sub_categories that indicate creative/media rather than foundation model
_CREATIVE_MEDIA_SUBCATS: set[str] = {
    "image-generation",
    "video-generation",
    "audio-speech",
    "music-generation",
    "3d-generation",
}

# ai-model tags that indicate creative/media
_CREATIVE_MEDIA_TAGS: set[str] = {
    "text-to-image",
    "text-to-video",
    "text-to-speech",
    "text-to-3d",
    "text-to-music",
    "image-to-video",
    "diffusion-model",
}

# ai-agent sub_categories that indicate dev platform
_AGENT_DEV_SUBCATS: set[str] = {
    "multi-agent-platform",
    "coding-agent",
}

# ai-app sub_categories that indicate enterprise vertical
_ENTERPRISE_VERTICAL_SUBCATS: set[str] = {
    "healthcare-medical",
    "education-tutoring",
    "finance-accounting",
    "legal",
}

# ── Tag mapping: old flat → new dimensional ─────────────────────────────────

_TAG_MAP: dict[str, str | None] = {
    # Direct mappings (same ID in new system)
    # technology
    "transformer": "transformer",
    "diffusion-model": "diffusion-model",
    "rag": "rag",
    "multimodal": "multimodal",
    "nlp": "nlp",
    "computer-vision": "computer-vision",
    "reinforcement-learning": "reinforcement-learning",
    "fine-tuning": "fine-tuning",
    "embedding": "embedding",
    "speech-to-text": "speech-to-text",
    "text-to-image": "text-to-image",
    "text-to-video": "text-to-video",
    "text-to-speech": "text-to-speech",
    "text-to-3d": "text-to-3d",
    "text-to-music": "text-to-music",
    "code-generation": "code-generation",
    "prompt-engineering": "prompt-engineering",
    "image-to-video": "image-to-video",
    # use_case
    "chatbot": "chatbot",
    "copilot": "copilot",
    "content-creation": "content-creation",
    "customer-support": "customer-support",
    "search-engine": "search-engine",
    "marketing": "marketing",
    # domain
    "drug-discovery": "drug-discovery",
    "medical-imaging": "medical-imaging",
    "protein-folding": "protein-folding",
    "clinical-trials": "clinical-trials",
    "trading": "trading",
    "risk-assessment": "risk-assessment",
    "fraud-detection": "fraud-detection",
    "defense": "defense",
    "self-driving": "self-driving",
    "humanoid-robot": "humanoid-robot",
    "drone": "drone",
    # business_model
    "open-source": "open-source",
    "saas": "saas",
    "freemium": "freemium",
    "enterprise": "enterprise",
    "cloud-native": "cloud-native",
    "closed-source": "closed-source",
    "b2b": "b2b",
    "b2c": "b2c",
    # technical
    "real-time": "real-time",
    "low-latency": "low-latency",
    "high-throughput": "high-throughput",
    "on-device": "on-device",
    "edge-ai": "edge-ai",
    "mobile-app": "mobile-app",
    "desktop-app": "desktop-app",
    "browser-extension": "browser-extension",
    "api-platform": "api-platform",
    "sdk": "sdk",
    "cli-tool": "cli-tool",
    # special
    "unicorn": "unicorn",
    "decacorn": "decacorn",
    "yc-backed": "yc-backed",
    "china": "china",
    "us": "us",
    "europe": "europe",
    "japan": "japan",
    "korea": "korea",
    # Renamed tags
    "developer-tools": "developers",
    "open-weights": "open-source",
    # Scraper-specific tags to map
    "ai-chatbots": "chatbot",
    # Dropped tags (not in new 114 vocabulary)
    "generative-ai": None,
    "startup": None,
    "hardware": None,
    "agents": None,
    "data-labeling": None,
    "synthetic-data": None,
    "vector-database": None,
    "model-serving": None,
    "mlops": None,
    "gpu-cloud": None,
    "inference": None,
    "safety": None,
    "alignment": None,
    "governance": None,
    "privacy": None,
    "series-a": None,
}


def _load_valid_tags() -> set[str]:
    """Load all valid tag IDs from the new dimensional tags.json."""
    data = json.loads(TAGS_FILE.read_text(encoding="utf-8"))
    valid: set[str] = set()
    for dim in data["dimensions"].values():
        for tag in dim["tags"]:
            valid.add(tag["id"])
    return valid


def _map_category(product: dict[str, Any]) -> str:
    """Map old category to new category using sub_category and tags heuristics."""
    old_cat = product.get("category", "")
    sub_cat = product.get("sub_category", "")
    tags = set(product.get("tags", []))

    # Direct 1:1 mappings
    if old_cat in _CATEGORY_MAP:
        return _CATEGORY_MAP[old_cat]

    # ai-model → ai-foundation-model or ai-creative-media
    if old_cat == "ai-model":
        if sub_cat in _CREATIVE_MEDIA_SUBCATS:
            return "ai-creative-media"
        if tags & _CREATIVE_MEDIA_TAGS:
            return "ai-creative-media"
        return "ai-foundation-model"

    # ai-app → ai-application or ai-enterprise-vertical
    if old_cat == "ai-app":
        if sub_cat in _ENTERPRISE_VERTICAL_SUBCATS:
            return "ai-enterprise-vertical"
        return "ai-application"

    # ai-agent → ai-application or ai-dev-platform
    if old_cat == "ai-agent":
        if sub_cat in _AGENT_DEV_SUBCATS:
            return "ai-dev-platform"
        return "ai-application"

    # Fallback
    return "ai-application"


def _map_tags(old_tags: list[str], valid_tags: set[str]) -> list[str]:
    """Map old flat tags to new dimensional tag IDs."""
    new_tags: list[str] = []
    seen: set[str] = set()

    for tag in old_tags:
        if tag in _TAG_MAP:
            mapped = _TAG_MAP[tag]
            if mapped and mapped not in seen:
                new_tags.append(mapped)
                seen.add(mapped)
        elif tag in valid_tags and tag not in seen:
            # Tag is already valid in new system
            new_tags.append(tag)
            seen.add(tag)
        # else: drop unknown tags silently

    return new_tags


def _infer_tags(product: dict[str, Any], existing_tags: set[str]) -> list[str]:
    """Infer additional tags from product fields."""
    inferred: list[str] = []

    # open_source → open-source tag
    if product.get("open_source") is True and "open-source" not in existing_tags:
        inferred.append("open-source")

    # pricing.model → business model tags
    pricing_model = product.get("pricing", {}).get("model", "")
    if pricing_model == "freemium" and "freemium" not in existing_tags:
        inferred.append("freemium")
    elif pricing_model == "open-source" and "open-source" not in existing_tags:
        inferred.append("open-source")

    # Country → special tags
    country = product.get("company", {}).get("headquarters", {}).get("country", "")
    country_map = {
        "China": "china",
        "United States": "us",
        "Japan": "japan",
        "South Korea": "korea",
    }
    for country_name, tag in country_map.items():
        if country == country_name and tag not in existing_tags:
            inferred.append(tag)

    # European countries → europe tag
    european = {
        "United Kingdom",
        "Germany",
        "France",
        "Sweden",
        "Norway",
        "Finland",
        "Denmark",
        "Netherlands",
        "Belgium",
        "Switzerland",
        "Austria",
        "Italy",
        "Spain",
        "Portugal",
        "Ireland",
        "Poland",
        "Czech Republic",
        "Romania",
        "Hungary",
        "Estonia",
        "Latvia",
        "Lithuania",
    }
    if country in european and "europe" not in existing_tags:
        inferred.append("europe")

    # Funding valuation → unicorn/decacorn
    valuation = (
        product.get("company", {}).get("funding", {}).get("valuation_usd", 0) or 0
    )
    if valuation >= 10_000_000_000 and "decacorn" not in existing_tags:
        inferred.append("decacorn")
    elif valuation >= 1_000_000_000 and "unicorn" not in existing_tags:
        inferred.append("unicorn")

    # api_available → api-service
    if (
        product.get("api_available") is True
        and "api-platform" not in existing_tags
        and "api-service" not in existing_tags
    ):
        inferred.append("api-service")

    # architecture → technology tags
    arch = (product.get("architecture") or "").lower()
    if "transformer" in arch and "transformer" not in existing_tags:
        inferred.append("transformer")
    if ("moe" in arch or "mixture" in arch) and "moe" not in existing_tags:
        inferred.append("moe")
    if "diffusion" in arch and "diffusion-model" not in existing_tags:
        inferred.append("diffusion-model")

    # modalities → multimodal
    modalities = product.get("modalities", [])
    if len(modalities) > 1 and "multimodal" not in existing_tags:
        inferred.append("multimodal")

    return inferred


def migrate_product(
    product: dict[str, Any], valid_tags: set[str]
) -> tuple[dict[str, Any], list[str]]:
    """Migrate a single product. Returns (updated_product, changes_list)."""
    changes: list[str] = []

    # 1. Map category
    old_cat = product.get("category", "")
    new_cat = _map_category(product)
    if old_cat != new_cat:
        product["category"] = new_cat
        changes.append(f"category: {old_cat} → {new_cat}")

    # 2. Map tags
    old_tags = product.get("tags", [])
    new_tags = _map_tags(old_tags, valid_tags)

    # 3. Infer additional tags
    inferred = _infer_tags(product, set(new_tags))
    new_tags.extend(inferred)

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for t in new_tags:
        if t not in seen:
            deduped.append(t)
            seen.add(t)
    new_tags = deduped

    if old_tags != new_tags:
        product["tags"] = new_tags
        added = set(new_tags) - set(old_tags)
        removed = set(old_tags) - set(new_tags)
        if added:
            changes.append(f"tags added: {', '.join(sorted(added))}")
        if removed:
            changes.append(f"tags removed: {', '.join(sorted(removed))}")

    return product, changes


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    if not PRODUCTS_DIR.exists():
        print(f"Products directory not found: {PRODUCTS_DIR}")
        sys.exit(1)

    valid_tags = _load_valid_tags()
    print(f"Loaded {len(valid_tags)} valid tags from {TAGS_FILE.name}")

    product_files = sorted(PRODUCTS_DIR.glob("*.json"))
    print(f"Found {len(product_files)} product files to migrate\n")

    total_changed = 0
    category_changes: dict[str, int] = {}
    tags_added_total = 0
    tags_removed_total = 0

    for filepath in product_files:
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  SKIP {filepath.name} (invalid JSON)")
            continue

        old_tags = set(data.get("tags", []))
        product, changes = migrate_product(data, valid_tags)

        if changes:
            total_changed += 1
            new_tags = set(product.get("tags", []))
            tags_added_total += len(new_tags - old_tags)
            tags_removed_total += len(old_tags - new_tags)

            # Track category changes
            for c in changes:
                if c.startswith("category:"):
                    old_new = c.split(": ")[1]
                    category_changes[old_new] = category_changes.get(old_new, 0) + 1

            if dry_run:
                print(f"  {filepath.name}:")
                for c in changes:
                    print(f"    {c}")
            else:
                filepath.write_text(
                    json.dumps(product, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:")
    print(f"  Total products: {len(product_files)}")
    print(f"  Changed: {total_changed}")
    print(f"  Tags added: {tags_added_total}")
    print(f"  Tags removed: {tags_removed_total}")

    if category_changes:
        print("\n  Category migrations:")
        for change, count in sorted(category_changes.items()):
            print(f"    {change}: {count}")


if __name__ == "__main__":
    main()
