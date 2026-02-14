"""Crunchbase scraper via Firecrawl for company funding data.

T1 Authoritative source — Crunchbase is the de facto standard for
startup funding data. Uses Firecrawl to scrape public organization
pages, bypassing the paid API ($3,000+/year).
"""

from __future__ import annotations

import json
import logging
import re

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.config import PRODUCTS_DIR

logger = logging.getLogger(__name__)

# Crunchbase organization page URL template
CB_ORG_URL = "https://www.crunchbase.com/organization/{slug}"

# Patterns for extracting data from Crunchbase markdown
_FUNDING_PATTERN = re.compile(
    r"(?:Total Funding|Funding Total)[:\s]*\$?([\d,.]+[MBK]?)", re.IGNORECASE
)
_VALUATION_PATTERN = re.compile(
    r"(?:Valuation|Post-Money Valuation)[:\s]*\$?([\d,.]+[MBT]?)", re.IGNORECASE
)
_LAST_ROUND_PATTERN = re.compile(
    r"(?:Last Funding Type|Latest Round)[:\s]*(Series [A-Z]|Seed|Pre-Seed|IPO|"
    r"Grant|Debt|Convertible|Growth|Venture|Angel|Private Equity)",
    re.IGNORECASE,
)
_EMPLOYEES_PATTERN = re.compile(
    r"(?:Number of Employees|Employees)[:\s]*([\d,]+-[\d,]+|[\d,]+\+?)", re.IGNORECASE
)
_FOUNDED_PATTERN = re.compile(r"(?:Founded Date|Founded)[:\s]*(\d{4})", re.IGNORECASE)
_HQ_PATTERN = re.compile(r"(?:Headquarters|HQ)[:\s]*([^|\n]+)", re.IGNORECASE)
_INVESTORS_PATTERN = re.compile(
    r"(?:Investors?|Key Investors?)[:\s]*([^\n]+)", re.IGNORECASE
)


class CrunchbaseScraper(BaseScraper):
    """Scrape Crunchbase organization pages via Firecrawl.

    Reads existing product JSON files that have a company.social.crunchbase
    URL, then scrapes those pages for funding, headquarter, and employee data.
    Falls back gracefully if Firecrawl is not configured.
    """

    @property
    def source_name(self) -> str:
        return "crunchbase"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T1_AUTHORITATIVE

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Scrape Crunchbase pages for existing products that have CB URLs."""
        try:
            from scrapers.utils.firecrawl_client import FirecrawlClient
        except ImportError:
            logger.info("Firecrawl not available, skipping Crunchbase scraper.")
            return []

        targets = self._collect_targets(limit)
        if not targets:
            logger.info("No Crunchbase URLs found in existing products.")
            return []

        fc = FirecrawlClient()
        products: list[ScrapedProduct] = []

        try:
            for product_name, cb_url in targets:
                if fc.remaining_quota <= 0:
                    logger.warning(
                        "Firecrawl daily quota exhausted, stopping. "
                        "Scraped %d/%d Crunchbase pages.",
                        len(products),
                        len(targets),
                    )
                    break

                result = fc.scrape_url(cb_url, formats=["markdown"])
                if not result.success:
                    logger.debug("Crunchbase %s: %s", cb_url, result.error)
                    continue

                product = self._parse_crunchbase_markdown(
                    product_name, cb_url, result.markdown
                )
                if product:
                    products.append(product)

                if len(products) >= limit:
                    break

        finally:
            fc.close()

        return products

    def _collect_targets(self, limit: int) -> list[tuple[str, str]]:
        """Collect Crunchbase URLs from existing product JSON files."""
        targets: list[tuple[str, str]] = []

        if not PRODUCTS_DIR.exists():
            return targets

        for filepath in sorted(PRODUCTS_DIR.glob("*.json")):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            name = data.get("name", "")
            company = data.get("company", {})

            # Check for explicit Crunchbase URL
            cb_url = company.get("social", {}).get("crunchbase", "")
            if not cb_url:
                # Try to construct from company name
                company_name = company.get("name", "")
                if company_name:
                    slug = _slugify_for_crunchbase(company_name)
                    cb_url = CB_ORG_URL.format(slug=slug)

            if cb_url and name:
                targets.append((name, cb_url))

            if len(targets) >= limit:
                break

        return targets

    def _parse_crunchbase_markdown(
        self, product_name: str, cb_url: str, markdown: str
    ) -> ScrapedProduct | None:
        """Extract structured data from Crunchbase markdown output."""
        if not markdown or len(markdown) < 50:
            return None

        # Extract funding total
        total_raised = _parse_money(_FUNDING_PATTERN, markdown)

        # Extract valuation
        valuation = _parse_money(_VALUATION_PATTERN, markdown)

        # Extract last round type
        last_round = None
        match = _LAST_ROUND_PATTERN.search(markdown)
        if match:
            last_round = match.group(1).strip().lower().replace(" ", "-")

        # Extract employee count
        employee_range = None
        match = _EMPLOYEES_PATTERN.search(markdown)
        if match:
            employee_range = _normalize_employee_range(match.group(1))

        # Extract founded year
        founded_year = None
        match = _FOUNDED_PATTERN.search(markdown)
        if match:
            year = int(match.group(1))
            if 1900 <= year <= 2026:
                founded_year = year

        # Extract headquarters
        hq_city = None
        hq_country = None
        match = _HQ_PATTERN.search(markdown)
        if match:
            hq_city, hq_country = _parse_headquarters(match.group(1))

        # Extract investors
        investors: list[str] = []
        match = _INVESTORS_PATTERN.search(markdown)
        if match:
            raw = match.group(1)
            investors = [inv.strip() for inv in raw.split(",") if inv.strip()][:10]

        # Only create product if we got meaningful data
        if not total_raised and not founded_year and not employee_range:
            return None

        return ScrapedProduct(
            name=product_name,
            source="crunchbase",
            source_url=cb_url,
            source_tier=SourceTier.T1_AUTHORITATIVE,
            company_name=product_name,
            company_total_raised_usd=total_raised,
            company_last_round=last_round,
            company_founded_year=founded_year,
            company_headquarters_city=hq_city,
            company_headquarters_country=hq_country,
            company_employee_count_range=employee_range,
            status="active",
            extra={
                k: v
                for k, v in {
                    "crunchbase_url": cb_url,
                    "crunchbase_valuation_usd": (
                        str(int(valuation)) if valuation else None
                    ),
                    "crunchbase_investors": ", ".join(investors) if investors else None,
                }.items()
                if v
            },
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_money(pattern: re.Pattern[str], text: str) -> float | None:
    """Extract and parse a monetary value from text."""
    match = pattern.search(text)
    if not match:
        return None

    raw = match.group(1).replace(",", "").strip()

    multiplier = 1.0
    if raw.endswith("T"):
        multiplier = 1_000_000_000_000
        raw = raw[:-1]
    elif raw.endswith("B"):
        multiplier = 1_000_000_000
        raw = raw[:-1]
    elif raw.endswith("M"):
        multiplier = 1_000_000
        raw = raw[:-1]
    elif raw.endswith("K"):
        multiplier = 1_000
        raw = raw[:-1]

    try:
        return float(raw) * multiplier
    except ValueError:
        return None


def _normalize_employee_range(raw: str) -> str | None:
    """Normalize a Crunchbase employee count to a standard range."""
    raw = raw.replace(",", "").strip()

    if "-" in raw:
        parts = raw.split("-")
        try:
            int(parts[0])
            high = int(parts[1].rstrip("+"))
        except ValueError:
            return raw
        if high <= 10:
            return "1-10"
        if high <= 50:
            return "11-50"
        if high <= 200:
            return "51-200"
        if high <= 500:
            return "201-500"
        if high <= 1000:
            return "501-1000"
        if high <= 5000:
            return "1001-5000"
        return "5001+"

    return raw


def _parse_headquarters(raw: str) -> tuple[str | None, str | None]:
    """Parse a Crunchbase HQ string like 'San Francisco, California, US'."""
    parts = [p.strip() for p in raw.split(",")]
    city = parts[0] if parts else None
    country = parts[-1] if len(parts) > 1 else None
    return city, country


def _slugify_for_crunchbase(name: str) -> str:
    """Convert a company name to a Crunchbase-style slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")
