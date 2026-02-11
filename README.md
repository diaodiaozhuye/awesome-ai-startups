# AI Company Directory

[![Daily Scrape](https://github.com/ai-company-directory/ai-company-directory/actions/workflows/daily-scrape.yml/badge.svg)](https://github.com/ai-company-directory/ai-company-directory/actions/workflows/daily-scrape.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

English | [中文](README_ZH.md)

An **open-source, Git-native data repository** tracking AI startups and companies worldwide.

- **Data as Code**: Each company is a JSON file in `data/companies/`, version-controlled with full Git history
- **Automated Updates**: Python scrapers run daily via GitHub Actions, discovering new companies and enriching existing data
- **Static Website**: Next.js static site for local or custom-hosted use with search, filtering, comparison, and analytics
- **Community-Driven**: Add companies or data sources via Pull Requests

## Quick Start

### Browse the Data

Run the website locally:

```bash
cd website
npm install
npm run dev
```

Or browse the raw JSON files in [`data/companies/`](data/companies/).

### Use the CLI

```bash
# Install
pip install -e .

# Validate all company data
aiscrape validate

# View a company
aiscrape show openai

# Generate stats and index
aiscrape generate-stats

# Run scrapers (dry run)
aiscrape scrape --source github --dry-run

# Run all scrapers
aiscrape scrape --source all --limit 50
```

### Build the Website

```bash
cd website
npm install
npm run build    # Static export to out/
npx serve out    # Preview locally
```

## Project Structure

```
ai-company-directory/
├── data/
│   ├── companies/          # One JSON file per company (28 seed companies)
│   ├── schema/             # JSON Schema definition
│   ├── categories.json     # Category taxonomy (EN/ZH)
│   ├── tags.json           # Tag list
│   ├── index.json          # [Auto-generated] Lightweight company index
│   └── stats.json          # [Auto-generated] Aggregated statistics
├── scrapers/               # Python scraper framework
│   ├── sources/            # GitHub, Y Combinator, Product Hunt, etc.
│   ├── enrichment/         # Normalize, deduplicate, merge
│   ├── validation/         # JSON Schema validation
│   └── generators/         # Generate index.json and stats.json
├── website/                # Next.js static site (SSG)
├── tests/                  # pytest test suite
├── .github/workflows/      # CI/CD pipelines
└── scripts/                # Utility scripts
```

## Data Schema

Each company JSON file follows the schema defined in [`data/schema/company.schema.json`](data/schema/company.schema.json).

Key fields: `slug`, `name`, `description`, `website`, `category`, `founded_year`, `headquarters`, `funding`, `team`, `social`, `products`, `tags`, `open_source`, `status`.

## Scraper Architecture

```
[Source Scrapers] -> ScrapedCompany list
       |
[Normalizer] -> Standardize names/URLs/countries
       |
[Deduplicator] -> Match against existing data
       |
[Merger] -> Non-destructive merge (never overwrites manual edits)
       |
[Validator] -> JSON Schema check
       |
[Write to data/companies/*.json]
```

Available sources:
| Source | Status | API |
|--------|--------|-----|
| GitHub Trending | Active | REST API |
| Y Combinator | Active | Algolia API |
| Product Hunt | Active | GraphQL API |
| Crunchbase | Stub | REST API |
| TechCrunch | Stub | RSS |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding new companies via PR
- Adding new scraper sources
- Improving the website
- Reporting data issues

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Data | JSON flat files + JSON Schema |
| Scrapers | Python 3.11 + httpx + BeautifulSoup |
| CLI | Click |
| Website | Next.js 15 + React 19 + TypeScript |
| Styling | Tailwind CSS |
| Search | Fuse.js (client-side) |
| Charts | Recharts |
| CI/CD | GitHub Actions |
| Hosting | Local / Custom Hosting |

## License

MIT License. See [LICENSE](LICENSE).

Data is sourced from publicly available information. Company logos and trademarks belong to their respective owners.
