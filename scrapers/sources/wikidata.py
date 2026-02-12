"""Wikidata SPARQL scraper for AI company/product verification data.

T1 Authoritative source — provides high-trust factual data such as
founding year, headquarters, key people, and Wikipedia URLs.
"""

from __future__ import annotations

import time
from datetime import date
from typing import TYPE_CHECKING

from scrapers.base import BaseScraper, ScrapedProduct, SourceTier
from scrapers.config import DEFAULT_REQUEST_DELAY
from scrapers.utils import create_http_client

if TYPE_CHECKING:
    import httpx

# Wikidata SPARQL endpoint (public, no auth required)
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

# SPARQL query to find AI-related companies.
# P31  = instance of
# P279 = subclass of
# Q11660  = artificial intelligence
# Q4830453 = business enterprise
# We look for companies whose industry (P452) or field (P101) includes AI.
_SPARQL_AI_COMPANIES = """\
SELECT DISTINCT
  ?company ?companyLabel ?companyDescription
  ?inception ?hqLabel ?countryLabel ?countryCode
  ?website ?article
WHERE {{
  # Companies in AI-related industries
  {{
    ?company wdt:P31/wdt:P279* wd:Q4830453 .
    ?company wdt:P452 ?industry .
    ?industry wdt:P279* wd:Q11660 .
  }} UNION {{
    ?company wdt:P31/wdt:P279* wd:Q4830453 .
    ?company wdt:P101 ?field .
    ?field wdt:P279* wd:Q11660 .
  }}

  OPTIONAL {{ ?company wdt:P571 ?inception . }}
  OPTIONAL {{ ?company wdt:P159 ?hq . }}
  OPTIONAL {{ ?company wdt:P17 ?country . ?country wdt:P297 ?countryCode . }}
  OPTIONAL {{ ?company wdt:P856 ?website . }}
  OPTIONAL {{
    ?article schema:about ?company ;
             schema:inLanguage "en" ;
             schema:isPartOf <https://en.wikipedia.org/> .
  }}

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,zh" . }}
}}
LIMIT {limit}
"""

# SPARQL query to find founders/key people of a given company entity.
_SPARQL_KEY_PEOPLE = """\
SELECT ?personLabel ?positionLabel ?isFounder WHERE {{
  {{
    wd:{entity_id} wdt:P112 ?person .
    BIND(true AS ?isFounder)
    OPTIONAL {{ ?person wdt:P39 ?position . }}
  }} UNION {{
    wd:{entity_id} wdt:P169 ?person .
    BIND(false AS ?isFounder)
    BIND(wd:Q484876 AS ?position)  # CEO
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
}}
LIMIT 10
"""


class WikidataScraper(BaseScraper):
    """Scrape Wikidata for AI company factual data via SPARQL.

    This is a T1 authoritative source — data from Wikidata is considered
    highly trustworthy for structured facts (founding years, headquarters,
    key people, Wikipedia links).
    """

    @property
    def source_name(self) -> str:
        return "wikidata"

    @property
    def source_tier(self) -> SourceTier:
        return SourceTier.T1_AUTHORITATIVE

    def scrape(self, limit: int = 100) -> list[ScrapedProduct]:
        """Query Wikidata SPARQL for AI companies and return ScrapedProduct list."""
        client = create_http_client(timeout=60)
        products: list[ScrapedProduct] = []

        try:
            query = _SPARQL_AI_COMPANIES.format(limit=limit)
            response = client.get(
                WIKIDATA_SPARQL_URL,
                params={"query": query, "format": "json"},
                headers={"Accept": "application/sparql-results+json"},
            )

            if not response.is_success:
                return products

            data = response.json()
            bindings = data.get("results", {}).get("bindings", [])
            seen: set[str] = set()

            for row in bindings:
                name = _val(row, "companyLabel")
                if not name or name in seen:
                    continue
                seen.add(name)

                # Extract entity ID for optional key-people lookup
                entity_uri = _val(row, "company")
                entity_id = entity_uri.split("/")[-1] if entity_uri else ""

                # Parse founding year
                founded_year = _parse_year(_val(row, "inception"))

                # Wikipedia URL
                wiki_url = _val(row, "article")

                # Website
                website = _val(row, "website")

                product = ScrapedProduct(
                    name=name,
                    source="wikidata",
                    source_url=(
                        f"https://www.wikidata.org/wiki/{entity_id}"
                        if entity_id
                        else ""
                    ),
                    source_tier=SourceTier.T1_AUTHORITATIVE,
                    description=_val(row, "companyDescription"),
                    product_url=website,
                    company_name=name,
                    company_website=website,
                    company_wikipedia_url=wiki_url,
                    company_founded_year=founded_year,
                    company_headquarters_city=_val(row, "hqLabel"),
                    company_headquarters_country=_val(row, "countryLabel"),
                    company_headquarters_country_code=_val(row, "countryCode"),
                    key_people=self._fetch_key_people(client, entity_id),
                    status="active",
                )
                products.append(product)

                if len(products) >= limit:
                    break

                time.sleep(DEFAULT_REQUEST_DELAY)

        finally:
            client.close()

        return products

    def _fetch_key_people(
        self,
        client: httpx.Client,
        entity_id: str,
    ) -> tuple[dict[str, str | bool], ...]:
        """Fetch founders and CEO for a given Wikidata entity."""
        if not entity_id:
            return ()

        query = _SPARQL_KEY_PEOPLE.format(entity_id=entity_id)
        try:
            response = client.get(
                WIKIDATA_SPARQL_URL,
                params={"query": query, "format": "json"},
                headers={"Accept": "application/sparql-results+json"},
            )
            if not response.is_success:
                return ()

            bindings = response.json().get("results", {}).get("bindings", [])
            people: list[dict[str, str | bool]] = []
            seen_names: set[str] = set()

            for row in bindings:
                person_name = _val(row, "personLabel")
                if not person_name or person_name in seen_names:
                    continue
                seen_names.add(person_name)

                is_founder = _val(row, "isFounder") == "true"
                title = _val(row, "positionLabel") or (
                    "Co-founder" if is_founder else ""
                )

                people.append(
                    {
                        "name": person_name,
                        "title": title,
                        "is_founder": is_founder,
                    }
                )

            return tuple(people)
        except Exception:
            return ()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _val(row: dict, key: str) -> str | None:
    """Extract a value from a SPARQL result binding."""
    binding = row.get(key)
    if binding is None:
        return None
    value = binding.get("value", "")
    return value if value else None


def _parse_year(date_str: str | None) -> int | None:
    """Parse a year from a Wikidata date string like '2015-12-11T00:00:00Z'."""
    if not date_str:
        return None
    try:
        year = int(date_str[:4])
        current_year = date.today().year
        if 1900 <= year <= current_year:
            return year
    except (ValueError, IndexError):
        pass
    return None
