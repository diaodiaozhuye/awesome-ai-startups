"""CLI entry point for the AI Product Data scraper tools."""

from __future__ import annotations

import json
import sys

import click

from scrapers.config import PRODUCTS_DIR


@click.group()
def cli() -> None:
    """AI Product Data - Scraper & Data Management CLI."""


@cli.command()
@click.option(
    "--source",
    default="all",
    help=(
        "Source to scrape (comma-separated or 'all'): "
        "wikidata, crunchbase, huggingface, ycombinator, producthunt, "
        "techcrunch, arxiv, lmsys, openrouter, theresanaiforthat, "
        "toolify, aiji, google_play, app_store, papers_with_code, "
        "artificial_analysis, 36kr, pypi, npm, dockerhub, "
        "company_website, indeed, aijobs, zhipin, lagou, liepin"
    ),
)
@click.option("--limit", default=50, help="Maximum products to fetch per source")
@click.option("--dry-run", is_flag=True, help="Print results without writing files")
def scrape(source: str, limit: int, dry_run: bool) -> None:
    """Run scrapers to discover and update AI products."""
    from scrapers.enrichment import Deduplicator, Merger, Normalizer
    from scrapers.sources import ALL_SCRAPERS

    if source == "all":
        scrapers_to_run = list(ALL_SCRAPERS.values())
    else:
        names = [s.strip() for s in source.split(",")]
        unknown = [n for n in names if n not in ALL_SCRAPERS]
        if unknown:
            click.echo(
                f"Unknown source(s): {', '.join(unknown)}. "
                f"Available: {', '.join(ALL_SCRAPERS)}"
            )
            sys.exit(1)
        scrapers_to_run = [ALL_SCRAPERS[n] for n in names]

    normalizer = Normalizer()
    deduplicator = Deduplicator()
    merger = Merger()

    all_scraped: list = []
    for scraper_cls in scrapers_to_run:
        scraper = scraper_cls()
        click.echo(f"\n[{scraper.source_name}] Scraping up to {limit} products...")
        try:
            results = scraper.scrape(limit=limit)
            click.echo(f"[{scraper.source_name}] Found {len(results)} products")
            all_scraped.extend(results)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
            click.echo(f"[{scraper.source_name}] Error: {e}", err=True)
        except Exception:
            import traceback

            click.echo(
                f"[{scraper.source_name}] Unexpected error:\n{traceback.format_exc()}",
                err=True,
            )

    if not all_scraped:
        click.echo("\nNo products discovered.")
        return

    # Normalize
    normalized = [normalizer.normalize(p) for p in all_scraped]
    click.echo(f"\nNormalized {len(normalized)} products")

    # Deduplicate
    result = deduplicator.deduplicate(normalized)
    click.echo(
        f"New: {len(result.new_products)}, Updates: {len(result.updates_for_existing)}"
    )

    if dry_run:
        click.echo("\n[DRY RUN] Would create:")
        for p in result.new_products:
            click.echo(f"  + {p.name} ({p.source})")
        click.echo("\n[DRY RUN] Would update:")
        for slug, p in result.updates_for_existing:
            click.echo(f"  ~ {slug} <- {p.source}")
        return

    # Merge
    for product in result.new_products:
        from scrapers.utils import slugify

        slug = slugify(product.name)
        merger.create_new(slug, product)
        safe_name = product.name.encode("ascii", "replace").decode("ascii")
        click.echo(f"  Created: {safe_name}")

    for slug, product in result.updates_for_existing:
        merger.merge_update(slug, product)
        click.echo(f"  Updated: {slug}")

    click.echo("\nDone! Run 'aiscrape generate-stats' to update index and stats.")


@cli.command()
def validate() -> None:
    """Validate all product JSON files against the schema."""
    from scrapers.validation import IntegrityValidator, ProductSchemaValidator

    # Schema validation
    schema_validator = ProductSchemaValidator()
    results = schema_validator.validate_all()

    valid_count = sum(1 for r in results if r.valid)
    invalid_count = len(results) - valid_count

    for r in results:
        if r.valid:
            click.echo(f"  OK  {r.filepath.name}")
        else:
            click.echo(f"  FAIL {r.filepath.name}")
            for error in r.errors:
                click.echo(f"       - {error}")

    click.echo(
        f"\n{valid_count} valid, {invalid_count} invalid out of {len(results)} files"
    )

    # Integrity validation
    click.echo("\nChecking referential integrity...")
    integrity_validator = IntegrityValidator()
    integrity_errors = integrity_validator.validate_all()

    if integrity_errors:
        for ie in integrity_errors:
            click.echo(f"  INTEGRITY  {ie.product_slug}: {ie.message}")
        click.echo(f"\n{len(integrity_errors)} integrity error(s) found")
    else:
        click.echo("  All references are valid")

    if invalid_count > 0 or integrity_errors:
        sys.exit(1)


@cli.command("generate-stats")
def generate_stats() -> None:
    """Regenerate index.json and stats.json from product data."""
    from scrapers.generators import IndexGenerator, StatsGenerator

    click.echo("Generating index.json...")
    index_gen = IndexGenerator()
    products = index_gen.generate()
    click.echo(f"  Index: {len(products)} products")

    click.echo("Generating stats.json...")
    stats_gen = StatsGenerator()
    stats = stats_gen.generate()
    click.echo(
        f"  Stats: {stats['total_products']} products, "
        f"${stats['total_funding_usd']:,.0f} total funding"
    )

    click.echo("\nDone!")


@cli.command()
@click.argument("slug")
def show(slug: str) -> None:
    """Show data for a single product by slug."""
    from scrapers.utils import validate_slug

    try:
        slug = validate_slug(slug)
    except ValueError:
        click.echo(f"Invalid slug: {slug}")
        sys.exit(1)

    filepath = PRODUCTS_DIR / f"{slug}.json"
    if not filepath.exists():
        click.echo(f"Product not found: {slug}")
        sys.exit(1)

    data = json.loads(filepath.read_text(encoding="utf-8"))
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


@cli.command()
def quality() -> None:
    """Score all products for data quality and update their data_quality_score."""
    from scrapers.enrichment import QualityScorer

    if not PRODUCTS_DIR.exists():
        click.echo("Products directory does not exist.")
        sys.exit(1)

    scorer = QualityScorer()
    product_files = sorted(PRODUCTS_DIR.glob("*.json"))

    if not product_files:
        click.echo("No product files found.")
        return

    updated = 0
    for filepath in product_files:
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            click.echo(f"  SKIP {filepath.name} (invalid JSON)")
            continue

        score = scorer.score(data)
        meta = data.setdefault("meta", {})
        old_score = meta.get("data_quality_score")
        meta["data_quality_score"] = score

        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        if old_score != score:
            click.echo(f"  {filepath.name}: {old_score} -> {score}")
            updated += 1
        else:
            click.echo(f"  {filepath.name}: {score} (unchanged)")

    click.echo(f"\nScored {len(product_files)} products, {updated} updated")


@cli.command()
@click.option("--slug", default=None, help="Enrich a single product by slug")
@click.option(
    "--max-score",
    default=0.6,
    type=float,
    help="Only enrich products with score <= this",
)
@click.option("--limit", default=10, help="Maximum products to enrich")
@click.option("--dry-run", is_flag=True, help="Preview gaps without calling LLM")
@click.option(
    "--model", default=None, help="Anthropic model to use (default: claude-sonnet-4-5)"
)
def enrich(
    slug: str | None, max_score: float, limit: int, dry_run: bool, model: str | None
) -> None:
    """Enrich products with missing fields using LLM (requires ANTHROPIC_API_KEY)."""
    from scrapers.enrichment import LLMEnricher, QualityScorer
    from scrapers.enrichment.merger import TieredMerger

    if not PRODUCTS_DIR.exists():
        click.echo("Products directory does not exist.")
        sys.exit(1)

    # Collect candidate products
    if slug:
        from scrapers.utils import validate_slug

        try:
            slug = validate_slug(slug)
        except ValueError:
            click.echo(f"Invalid slug: {slug}")
            sys.exit(1)

        filepath = PRODUCTS_DIR / f"{slug}.json"
        if not filepath.exists():
            click.echo(f"Product not found: {slug}")
            sys.exit(1)
        candidates = [filepath]
    else:
        scorer = QualityScorer()
        candidates = []
        for filepath in sorted(PRODUCTS_DIR.glob("*.json")):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            score = scorer.score(data)
            if score <= max_score:
                candidates.append(filepath)
        candidates = candidates[:limit]

    if not candidates:
        click.echo("No products need enrichment.")
        return

    click.echo(f"Found {len(candidates)} product(s) to enrich")

    enricher_kwargs: dict[str, str] = {}
    if model:
        enricher_kwargs["model"] = model

    # LLMEnricher uses lazy client init — safe to construct without API key.
    # The key is only required when enrich() actually calls the LLM.
    enricher = LLMEnricher(**enricher_kwargs)

    if not dry_run:
        # Validate API key eagerly so we fail fast
        try:
            _ = enricher.client
        except (ImportError, ValueError) as e:
            click.echo(f"Error: {e}")
            sys.exit(1)

    merger = TieredMerger()
    enriched_count = 0

    for filepath in candidates:
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            click.echo(f"  SKIP {filepath.name} (invalid JSON)")
            continue

        product_slug = data.get("slug", filepath.stem)

        # Validate slug from JSON data to prevent path traversal
        from scrapers.utils import validate_slug as _validate_slug

        try:
            product_slug = _validate_slug(product_slug)
        except ValueError:
            click.echo(f"  SKIP {filepath.name} (invalid slug in data)")
            continue

        if dry_run:
            gaps = enricher.identify_gaps(data)
            if gaps:
                click.echo(f"  {product_slug}: {len(gaps)} gaps — {', '.join(gaps)}")
            else:
                click.echo(f"  {product_slug}: no gaps")
            continue

        click.echo(f"  Enriching {product_slug}...")
        scraped = enricher.enrich(data)
        if scraped is None:
            click.echo("    No enrichment needed or LLM returned nothing")
            continue

        merger.merge_update(product_slug, scraped)
        enriched_count += 1
        safe_name = product_slug.encode("ascii", "replace").decode("ascii")
        click.echo(f"    Enriched: {safe_name}")

    if dry_run:
        click.echo(f"\n[DRY RUN] {len(candidates)} products analyzed")
    else:
        click.echo(f"\nEnriched {enriched_count} out of {len(candidates)} products")


if __name__ == "__main__":
    cli()
