"""Path constants and configuration for scrapers."""

from __future__ import annotations

from pathlib import Path

# Root of the repository
REPO_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = REPO_ROOT / "data"
COMPANIES_DIR = DATA_DIR / "companies"
SCHEMA_DIR = DATA_DIR / "schema"

# New product-centric directories
PRODUCTS_DIR = DATA_DIR / "products"
ARCHIVE_DIR = DATA_DIR / "archive"

# Data files
SCHEMA_FILE = SCHEMA_DIR / "company.schema.json"
PRODUCT_SCHEMA_FILE = SCHEMA_DIR / "product.schema.json"
INDEX_FILE = DATA_DIR / "index.json"
STATS_FILE = DATA_DIR / "stats.json"
CATEGORIES_FILE = DATA_DIR / "categories.json"
TAGS_FILE = DATA_DIR / "tags.json"

# Discovery queue
DISCOVERY_QUEUE_FILE = DATA_DIR / "discovery_queue.json"

# Scraper settings
DEFAULT_LIMIT = 100
HTTP_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

# Crawl settings (slow and steady principle)
DEFAULT_REQUEST_DELAY = 5.0  # seconds between requests per domain
MAX_DAILY_FIRECRAWL_PAGES = 100
MAX_DAILY_FREE_API_REQUESTS = 500
MAX_DAILY_SCRAPY_PAGES = 200
SCRAPY_REQUEST_DELAY = 7.0  # seconds, slower for Chinese job sites
MAX_RETRIES_BEFORE_SKIP = 3
RETRY_MAX_WAIT = 300  # 5 minutes max wait on retry

# Job scraper settings
JOB_SCRAPER_RATE_LIMIT = (
    5.0  # seconds between requests (matches slow-and-steady principle)
)
JOB_SCRAPER_MAX_JOBS_PER_KEYWORD = 20

# User agent for HTTP requests
USER_AGENT = (
    "AIProductData/0.1 "
    "(https://github.com/diaodiaozhuye/awesome-ai-startups; open-source project)"
)
