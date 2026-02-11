# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Company Directory — an open-source, Git-native data repository tracking AI startups worldwide. Three layers: JSON data files, Python scraper/CLI tooling, and a Next.js static website.

## Commands

### Python (scrapers & CLI)

```bash
pip install -e ".[dev]"          # Install with dev dependencies (pytest, ruff, mypy)
aiscrape validate                # Validate all company JSONs against schema
aiscrape generate-stats          # Regenerate data/index.json and data/stats.json
aiscrape show <slug>             # Display a single company's data
aiscrape scrape --source github --dry-run   # Preview scraper output
aiscrape scrape --source all --limit 50     # Run all scrapers
```

```bash
pytest tests/ -v                             # Run all tests
pytest tests/test_normalizer.py -v           # Run a single test file
pytest tests/test_normalizer.py::test_name -v  # Run a single test
pytest --cov=scrapers --cov-report=term-missing  # Coverage report
ruff check scrapers/ tests/                  # Lint Python
mypy scrapers/ --ignore-missing-imports      # Type check
```

### Website (Next.js)

```bash
cd website && npm install        # Install frontend dependencies
npm run dev                      # Dev server with hot reload
npm run build                    # Static export to website/out/
npm run lint                     # ESLint
```

## Architecture

### Data Pipeline (Scraper → Disk)

```
Source Scrapers (scrapers/sources/)
  → ScrapedCompany (frozen dataclass)
  → Normalizer (scrapers/enrichment/normalizer.py)    — standardize URLs, names, countries
  → Deduplicator (scrapers/enrichment/deduplicator.py) — match via domain, slug, name similarity
  → Merger (scrapers/enrichment/merger.py)             — non-destructive merge (never overwrites manual edits)
  → SchemaValidator (scrapers/validation/)             — JSON Schema check
  → Write to data/companies/<slug>.json
```

New scrapers extend `BaseScraper` (scrapers/base.py) and register in `scrapers/sources/__init__.py`. The `ScrapedCompany` is a frozen dataclass — only `name` and `source` are required; the enrichment pipeline handles the rest.

### Generators

`IndexGenerator` and `StatsGenerator` (scrapers/generators/) produce `data/index.json` and `data/stats.json` — these are auto-generated and should not be manually edited. Run `aiscrape generate-stats` after data changes.

### Website

Next.js App Router with static export (`output: "export"` in next.config.ts). i18n via URL segments (`/en/`, `/zh/`). Client-side search powered by Fuse.js. Charts via Recharts. The website reads from `data/` at build time via `website/src/lib/data.ts`.

Key layout: `website/src/app/[locale]/` — all pages are under the locale dynamic segment. Components are organized under `website/src/components/` by domain (company, search, analytics, layout, ui).

## Data Schema

Company JSON files live in `data/companies/` and must conform to `data/schema/company.schema.json`.

Required fields: `slug`, `name`, `description` (min 10 chars), `website` (URI), `category` (enum), `founded_year`, `headquarters` (city + country).

Valid categories: `llm-foundation-model`, `ai-coding`, `ai-image-video`, `ai-audio-speech`, `ai-search`, `ai-robotics`, `ai-infrastructure`, `ai-data-analytics`, `ai-assistant`, `ai-enterprise`, `autonomous-vehicles`, `ai-security-defense`, `ai-healthcare`, `ai-education`, `ai-finance`, `ai-gaming`, `ai-other`.

The slug must match the filename (without `.json`) and follow pattern `^[a-z0-9-]+$`.

## CI/CD

- **validate-pr.yml**: On PRs — runs schema validation, ruff, mypy, website lint + build
- **daily-scrape.yml**: Scheduled — runs all scrapers and auto-commits updates

## Code Conventions

- Python 3.11+, PEP 8 via ruff (line length 100), mypy strict (`disallow_untyped_defs`)
- ruff rules: E, F, W, I, N, UP, B, SIM
- Frozen dataclasses for immutable data structures
- TypeScript strict mode for the website, Tailwind CSS for styling
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
