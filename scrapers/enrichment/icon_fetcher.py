"""Fetch product and company icons from various sources."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse


class IconFetcher:
    """Generate icon/logo URL candidates for products and companies.

    Strategies (in priority order):
    1. og:image meta tag from product URL (requires HTTP fetch)
    2. Favicon from product domain
    3. Clearbit Logo API (free, no auth needed)
    4. Google favicon service (fallback)

    This class generates candidate URLs. Actual HTTP validation
    (checking if URLs return valid images) should be done by the caller.
    """

    # Clearbit logo API (free, returns company logos by domain)
    _CLEARBIT_LOGO_URL = "https://logo.clearbit.com/{domain}"
    # Google favicon service
    _GOOGLE_FAVICON_URL = "https://www.google.com/s2/favicons?domain={domain}&sz=128"

    def get_icon_candidates(self, url: str | None) -> list[str]:
        """Generate ordered list of icon URL candidates for a given URL.

        Args:
            url: Product or company URL to extract icons from.

        Returns:
            List of candidate icon URLs, ordered by preference.
        """
        if not url:
            return []

        domain = self._extract_domain(url)
        if not domain:
            return []

        candidates: list[str] = []

        # Strategy 1: Favicon at root (most common)
        base_url = f"https://{domain}"
        candidates.append(urljoin(base_url, "/favicon.ico"))

        # Strategy 2: Apple touch icon (higher resolution)
        candidates.append(urljoin(base_url, "/apple-touch-icon.png"))

        # Strategy 3: Clearbit Logo API (free, no auth)
        candidates.append(self._CLEARBIT_LOGO_URL.format(domain=domain))

        # Strategy 4: Google favicon service (always works, lower quality)
        candidates.append(self._GOOGLE_FAVICON_URL.format(domain=domain))

        return candidates

    def get_company_logo_candidates(
        self, company_website: str | None, company_name: str | None = None
    ) -> list[str]:
        """Generate logo candidates for a company.

        Args:
            company_website: Company website URL.
            company_name: Company name (used for Clearbit lookup).

        Returns:
            List of candidate logo URLs.
        """
        candidates = self.get_icon_candidates(company_website)

        # If we have a company name, try Clearbit with common domain patterns
        if company_name and not company_website:
            slug = company_name.lower().replace(" ", "").replace("-", "")
            for tld in [".com", ".ai", ".io"]:
                domain = f"{slug}{tld}"
                candidates.append(self._CLEARBIT_LOGO_URL.format(domain=domain))

        return candidates

    @staticmethod
    def _extract_domain(url: str) -> str | None:
        """Extract domain from a URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc or parsed.path.split("/")[0]
        except (ValueError, AttributeError):
            return None
