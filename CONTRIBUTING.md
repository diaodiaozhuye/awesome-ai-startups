# Contributing Guide

Thank you for your interest in contributing to the AI Company Directory!

## Ways to Contribute

### 1. Add a New Company

The easiest way to contribute! Create a new JSON file in `data/companies/`:

1. Fork this repository
2. Create a new file `data/companies/<slug>.json` (slug = lowercase, hyphens only)
3. Follow the schema in `data/schema/company.schema.json`
4. Run `aiscrape validate` to check your file
5. Run `aiscrape generate-stats` to update index and stats
6. Submit a Pull Request

**Minimum required fields:**
```json
{
  "slug": "your-company",
  "name": "Your Company",
  "description": "A brief description of what this company does (at least 10 chars).",
  "website": "https://your-company.com",
  "category": "ai-other",
  "founded_year": 2024,
  "headquarters": {
    "city": "San Francisco",
    "country": "United States"
  }
}
```

### 2. Update Existing Data

Found outdated or incorrect data? Edit the relevant JSON file and submit a PR.

- Only change fields you have reliable sources for
- Add source URLs to `meta.sources` array
- Do NOT remove existing data unless it is clearly wrong

### 3. Add a New Scraper Source

1. Create a new file in `scrapers/sources/`
2. Extend `BaseScraper` and implement `source_name` and `scrape()`
3. Register it in `scrapers/sources/__init__.py`
4. Add tests in `tests/`
5. Submit a PR

### 4. Improve the Website

The website is in the `website/` directory using Next.js + TypeScript + Tailwind.

```bash
cd website
npm install
npm run dev    # Development server
npm run build  # Production build
```

### 5. Report Issues

Use the issue templates to report:
- Data errors or outdated information
- Website bugs
- Feature requests

## Development Setup

```bash
# Clone
git clone https://github.com/ai-company-directory/ai-company-directory.git
cd ai-company-directory

# Python setup
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Validate data
aiscrape validate

# Website setup
cd website && npm install && npm run dev
```

## Code Standards

- **Python**: PEP 8, type annotations, ruff for linting
- **TypeScript**: ESLint + Next.js defaults
- **Data**: Must pass JSON Schema validation
- **Commits**: Conventional commits (feat:, fix:, chore:, docs:)

## Review Process

1. All PRs are validated by CI (JSON Schema, linting, build)
2. Data PRs are reviewed for accuracy
3. Code PRs are reviewed for quality

Thank you for helping build the most comprehensive open-source AI company directory!
