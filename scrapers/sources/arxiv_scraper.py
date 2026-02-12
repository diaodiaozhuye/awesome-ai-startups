"""ArXiv paper scraper for AI model/product discovery.

T2 Open Web source — discovers new AI models and research products by
scanning recent papers on arxiv.org.  Primarily used for the discovery
phase: extracting model names from paper titles and metadata.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import date

import httpx

from scrapers.base import BaseScraper, DiscoveredName, ScrapedProduct, SourceTier
from scrapers.config import DEFAULT_REQUEST_DELAY
from scrapers.utils import create_http_client

logger = logging.getLogger(__name__)

# ArXiv API endpoint (public, no auth required)
ARXIV_API_URL = "https://export.arxiv.org/api/query"

# AI-related categories on ArXiv
ARXIV_AI_CATEGORIES = [
    "cs.AI",  # Artificial Intelligence
    "cs.CL",  # Computation and Language (NLP)
    "cs.CV",  # Computer Vision
    "cs.LG",  # Machine Learning
    "cs.NE",  # Neural and Evolutionary Computing
    "cs.RO",  # Robotics
    "stat.ML",  # Machine Learning (Statistics)
]

# Regex patterns for extracting model names from paper titles.
# Matches patterns like "ModelName: subtitle" or "We introduce ModelName,"
_MODEL_NAME_PATTERNS = [
    # "ModelName: A Large Language Model for ..."
    re.compile(r"^([A-Z][A-Za-z0-9.+-]+(?:\s[A-Z][A-Za-z0-9.+-]+){0,2}):\s"),
    # "... introducing ModelName, a ..."
    re.compile(
        r"[Ii]ntroduc(?:e|ing)\s+([A-Z][A-Za-z0-9.+-]+(?:\s[A-Z][A-Za-z0-9.+-]+){0,2})[,.]"
    ),
    # "... we present ModelName ..."
    re.compile(
        r"[Ww]e\s+present\s+([A-Z][A-Za-z0-9.+-]+(?:\s[A-Z][A-Za-z0-9.+-]+){0,2})\b"
    ),
    # "ModelName -- An Open ..."
    re.compile(r"^([A-Z][A-Za-z0-9.+-]+(?:\s[A-Z][A-Za-z0-9.+-]+){0,2})\s+--\s"),
]

# Common false positives to skip
_SKIP_NAMES = frozenset(
    {
        "A",
        "An",
        "The",
        "We",
        "In",
        "On",
        "For",
        "From",
        "To",
        "With",
        "Our",
        "This",
        "New",
        "Large",
        "Language",
        "Model",
        "Vision",
        "Towards",
        "Learning",
        "Deep",
        "Neural",
        "Data",
        "Self",
        "Multi",
        "Pre",
        "Open",
        "Efficient",
        "Scaling",
        "How",
        "Survey",
        "Review",
        "Benchmark",
        "Beyond",
        "Exploring",
    }
)


class ArXivScraper(BaseScraper):
    """Scrape ArXiv for recent AI papers to discover model/product names.

    This scraper serves a dual purpose:
    1. **Discovery**: Extract model names from paper titles
    2. **Enrichment**: Provide paper metadata (title, authors, abstract, dates)

    The slow-crawl principle is built in: ArXiv rate-limits to 1 request
    per 3 seconds; we default to DEFAULT_REQUEST_DELAY (5s).
    """

    @property
    def source_name(self) -> str:
        return "arxiv"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T2_OPEN_WEB

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Fetch recent AI papers and extract model information."""
        client = create_http_client(timeout=30)
        products: list[ScrapedProduct] = []
        seen: set[str] = set()
        today = date.today().isoformat()

        try:
            for category in ARXIV_AI_CATEGORIES:
                if len(products) >= limit:
                    break

                papers = self._fetch_papers(client, category, max_results=50)

                for paper in papers:
                    model_name = self._extract_model_name(paper.get("title", ""))
                    if not model_name or model_name.lower() in seen:
                        continue
                    seen.add(model_name.lower())

                    product = self._paper_to_product(paper, model_name, today)
                    products.append(product)

                    if len(products) >= limit:
                        break

                time.sleep(DEFAULT_REQUEST_DELAY)

        finally:
            client.close()

        return products

    def discover(self, limit: int = 100) -> list[DiscoveredName]:
        """Lightweight discovery: extract model names from recent papers."""
        client = create_http_client(timeout=30)
        names: list[DiscoveredName] = []
        seen: set[str] = set()

        try:
            for category in ARXIV_AI_CATEGORIES:
                if len(names) >= limit:
                    break

                papers = self._fetch_papers(client, category, max_results=50)

                for paper in papers:
                    model_name = self._extract_model_name(paper.get("title", ""))
                    if not model_name or model_name.lower() in seen:
                        continue
                    seen.add(model_name.lower())

                    names.append(
                        DiscoveredName(
                            name=model_name,
                            source="arxiv",
                            source_url=paper.get("link", ""),
                            discovered_at=date.today().isoformat(),
                        )
                    )

                    if len(names) >= limit:
                        break

                time.sleep(DEFAULT_REQUEST_DELAY)

        finally:
            client.close()

        return names

    def _fetch_papers(
        self,
        client: httpx.Client,
        category: str,
        max_results: int = 50,
    ) -> list[dict]:
        """Fetch recent papers from a given ArXiv category."""
        try:
            response = client.get(
                ARXIV_API_URL,
                params={
                    "search_query": f"cat:{category}",
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                    "start": 0,
                    "max_results": max_results,
                },
            )

            if not response.is_success:
                return []

            return self._parse_atom_feed(response.text)

        except (httpx.HTTPError, httpx.TimeoutException, OSError) as exc:
            logger.debug("ArXiv query failed for %s: %s", category, exc)
            return []

    def _parse_atom_feed(self, xml_text: str) -> list[dict]:
        """Parse ArXiv Atom XML feed into a list of paper dicts.

        Uses basic XML parsing to avoid heavy dependencies.
        """
        papers: list[dict] = []

        # Split entries
        entries = xml_text.split("<entry>")[1:]  # skip feed header

        for entry_xml in entries:
            paper: dict[str, str | list[str]] = {}

            # Title
            title_match = re.search(r"<title>(.*?)</title>", entry_xml, re.DOTALL)
            if title_match:
                paper["title"] = _clean_text(title_match.group(1))

            # Summary / abstract
            summary_match = re.search(r"<summary>(.*?)</summary>", entry_xml, re.DOTALL)
            if summary_match:
                paper["summary"] = _clean_text(summary_match.group(1))

            # Link (abs page)
            link_match = re.search(
                r"<id>(https?://arxiv\.org/abs/[^<]+)</id>", entry_xml
            )
            if link_match:
                paper["link"] = link_match.group(1)

            # Published date
            published_match = re.search(r"<published>(.*?)</published>", entry_xml)
            if published_match:
                paper["published"] = published_match.group(1)[:10]  # YYYY-MM-DD

            # Authors
            authors = re.findall(r"<name>(.*?)</name>", entry_xml)
            if authors:
                paper["authors"] = authors

            # Categories
            categories = re.findall(r'<category[^>]*term="([^"]+)"', entry_xml)
            if categories:
                paper["categories"] = categories

            if paper.get("title"):
                papers.append(paper)

        return papers

    def _extract_model_name(self, title: str) -> str | None:
        """Try to extract a model/product name from a paper title."""
        for pattern in _MODEL_NAME_PATTERNS:
            match = pattern.search(title)
            if match:
                name = match.group(1).strip()
                # Validate: not a stop word, not too short, not too long
                if (
                    name not in _SKIP_NAMES
                    and len(name) >= 2
                    and len(name) <= 50
                    and not name.isupper()  # Skip all-caps acronyms like "NLP"
                ):
                    return name
        return None

    def _paper_to_product(
        self, paper: dict, model_name: str, today: str
    ) -> ScrapedProduct:
        """Convert a parsed paper dict into a ScrapedProduct."""
        authors = paper.get("authors", [])
        categories = paper.get("categories", [])

        # Determine sub_category from ArXiv categories
        sub_category = None
        for cat in categories:
            if cat in ("cs.CL",):
                sub_category = "text-generation"
                break
            if cat in ("cs.CV",):
                sub_category = "image-generation"
                break
            if cat in ("cs.RO",):
                sub_category = None  # robotics doesn't map directly
                break

        # Build key people from first few authors
        key_people: list[dict[str, str | bool]] = []
        for author_name in authors[:5]:
            if isinstance(author_name, str):
                key_people.append(
                    {"name": author_name, "title": "Author", "is_founder": False}
                )

        tags = ["research"]
        if "cs.CL" in categories:
            tags.append("nlp")
        if "cs.CV" in categories:
            tags.append("computer-vision")
        if "cs.LG" in categories:
            tags.append("machine-learning")

        # Determine product_type from ArXiv categories
        product_type = "other"
        for cat in categories:
            if cat in ("cs.CL",):
                product_type = "llm"
                break
            if cat in ("cs.CV", "cs.AI", "cs.LG", "cs.NE"):
                product_type = "other"
                break

        return ScrapedProduct(
            name=model_name,
            source="arxiv",
            source_url=paper.get("link", ""),
            source_tier=SourceTier.T2_OPEN_WEB,
            description=paper.get("summary"),
            product_type=product_type,
            category="ai-model",
            sub_category=sub_category,
            tags=tuple(tags),
            key_people=tuple(key_people),
            release_date=paper.get("published"),
            status="active",
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clean_text(text: str) -> str:
    """Clean whitespace from extracted XML text."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()
