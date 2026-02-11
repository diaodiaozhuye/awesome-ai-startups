"""CLI entry point for the AI Product Data scraper tools."""

from __future__ import annotations

import json
import sys

import click

from scrapers.config import COMPANIES_DIR


@click.group()
def cli() -> None:
    """AI Product Data - Scraper & Data Management CLI."""


@cli.command()
@click.option(
    "--source",
    default="all",
    help=(
        "Source to scrape (comma-separated or 'all'): "
        "github, ycombinator, producthunt, crunchbase, techcrunch, "
        "indeed, aijobs, linkedin-jobs, glassdoor, zhipin, lagou, liepin"
    ),
)
@click.option("--limit", default=50, help="Maximum companies to fetch per source")
@click.option("--dry-run", is_flag=True, help="Print results without writing files")
def scrape(source: str, limit: int, dry_run: bool) -> None:
    """Run scrapers to discover and update AI companies."""
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

    all_scraped = []
    for scraper_cls in scrapers_to_run:
        scraper = scraper_cls()
        click.echo(f"\n[{scraper.source_name}] Scraping up to {limit} companies...")
        try:
            results = scraper.scrape(limit=limit)
            click.echo(f"[{scraper.source_name}] Found {len(results)} companies")
            all_scraped.extend(results)
        except Exception as e:
            click.echo(f"[{scraper.source_name}] Error: {e}")

    if not all_scraped:
        click.echo("\nNo companies discovered.")
        return

    # Normalize
    normalized = [normalizer.normalize(c) for c in all_scraped]
    click.echo(f"\nNormalized {len(normalized)} companies")

    # Deduplicate
    result = deduplicator.deduplicate(normalized)
    click.echo(
        f"New: {len(result.new_companies)}, Updates: {len(result.updates_for_existing)}"
    )

    if dry_run:
        click.echo("\n[DRY RUN] Would create:")
        for c in result.new_companies:
            click.echo(f"  + {c.name} ({c.source})")
        click.echo("\n[DRY RUN] Would update:")
        for slug, c in result.updates_for_existing:
            click.echo(f"  ~ {slug} <- {c.source}")
        return

    # Merge
    for company in result.new_companies:
        merger.create_new(company)
        safe_name = company.name.encode("ascii", "replace").decode("ascii")
        click.echo(f"  Created: {safe_name}")

    for slug, company in result.updates_for_existing:
        merger.merge_update(slug, company)
        click.echo(f"  Updated: {slug}")

    click.echo("\nDone! Run 'aiscrape generate-stats' to update index and stats.")


@cli.command()
def validate() -> None:
    """Validate all company JSON files against the schema."""
    from scrapers.validation import SchemaValidator

    validator = SchemaValidator()
    results = validator.validate_all()

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

    if invalid_count > 0:
        sys.exit(1)


@cli.command("generate-stats")
def generate_stats() -> None:
    """Regenerate index.json and stats.json from company data."""
    from scrapers.generators import IndexGenerator, StatsGenerator

    click.echo("Generating index.json...")
    index_gen = IndexGenerator()
    companies = index_gen.generate()
    click.echo(f"  Index: {len(companies)} companies")

    click.echo("Generating stats.json...")
    stats_gen = StatsGenerator()
    stats = stats_gen.generate()
    click.echo(
        f"  Stats: {stats['total_companies']} companies, "
        f"${stats['total_funding_usd']:,.0f} total funding"
    )

    click.echo("\nDone!")


@cli.command()
@click.argument("slug")
def show(slug: str) -> None:
    """Show data for a single company by slug."""
    filepath = COMPANIES_DIR / f"{slug}.json"
    if not filepath.exists():
        click.echo(f"Company not found: {slug}")
        sys.exit(1)

    data = json.loads(filepath.read_text(encoding="utf-8"))
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli()
