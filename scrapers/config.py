"""Path constants and configuration for scrapers."""

from __future__ import annotations

from pathlib import Path

# Root of the repository
REPO_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = REPO_ROOT / "data"
COMPANIES_DIR = DATA_DIR / "companies"
SCHEMA_DIR = DATA_DIR / "schema"

# Data files
SCHEMA_FILE = SCHEMA_DIR / "company.schema.json"
INDEX_FILE = DATA_DIR / "index.json"
STATS_FILE = DATA_DIR / "stats.json"
CATEGORIES_FILE = DATA_DIR / "categories.json"
TAGS_FILE = DATA_DIR / "tags.json"

# Scraper settings
DEFAULT_LIMIT = 100
HTTP_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

# Job scraper settings
JOB_SCRAPER_RATE_LIMIT = 3.0  # seconds between requests
JOB_SCRAPER_MAX_JOBS_PER_KEYWORD = 20

# User agent for HTTP requests
USER_AGENT = (
    "AICompanyDirectory/0.1 "
    "(https://github.com/ai-company-directory; open-source project)"
)
