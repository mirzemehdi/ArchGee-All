"""Adzuna API adapter for fetching architecture jobs worldwide."""

from typing import List, Optional
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from adapters.base import BaseAdapter
from config import config
from models.job import ScrapedJob
from utils.logger import get_logger

logger = get_logger(__name__)

# All Adzuna-supported countries with their local currency
ADZUNA_COUNTRIES = {
    "gb": {"name": "Great Britain", "currency": "GBP"},
    "us": {"name": "United States", "currency": "USD"},
    "au": {"name": "Australia", "currency": "AUD"},
    "ca": {"name": "Canada", "currency": "CAD"},
    "de": {"name": "Germany", "currency": "EUR"},
    "fr": {"name": "France", "currency": "EUR"},
    "in": {"name": "India", "currency": "INR"},
    "nl": {"name": "Netherlands", "currency": "EUR"},
    "nz": {"name": "New Zealand", "currency": "NZD"},
    "sg": {"name": "Singapore", "currency": "SGD"},
    "za": {"name": "South Africa", "currency": "ZAR"},
    "at": {"name": "Austria", "currency": "EUR"},
    "br": {"name": "Brazil", "currency": "BRL"},
    "it": {"name": "Italy", "currency": "EUR"},
    "pl": {"name": "Poland", "currency": "PLN"},
}


class AdzunaAdapter(BaseAdapter):
    """Fetches architecture jobs from the Adzuna API worldwide.

    Adzuna provides a REST API for job search across 15+ countries.
    Docs: https://developer.adzuna.com/docs/search
    """

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_key: Optional[str] = None,
    ):
        self.app_id = app_id or config.ADZUNA_APP_ID
        self.app_key = app_key or config.ADZUNA_APP_KEY
        self.client = httpx.Client(timeout=30.0)

    @property
    def source_name(self) -> str:
        return "adzuna"

    def fetch_jobs(
        self,
        keywords: List[str],
        location: str = "",
        max_results: int = 100,
        country: str = "all",
    ) -> List[ScrapedJob]:
        """Fetch jobs from Adzuna API.

        Args:
            keywords: Search keywords.
            location: Location filter (only used when country is a single code).
            max_results: Max results to fetch per country.
            country: Two-letter country code, comma-separated codes, or "all" for worldwide.

        Returns:
            List of ScrapedJob instances from all requested countries.
        """
        if not self.app_id or not self.app_key:
            logger.warning("[adzuna] No API credentials configured, skipping.")
            return []

        countries = self._resolve_countries(country)

        self._log_fetch_start(keywords, f"{len(countries)} countries")

        all_jobs: List[ScrapedJob] = []

        for cc in countries:
            country_name = ADZUNA_COUNTRIES[cc]["name"]
            logger.info(f"[adzuna] Fetching from {country_name} ({cc})...")

            country_jobs = self._fetch_country(
                keywords=keywords,
                location=location if len(countries) == 1 else "",
                country=cc,
                max_results=max_results,
            )

            logger.info(f"[adzuna] {country_name}: {len(country_jobs)} jobs")
            all_jobs.extend(country_jobs)

        self._log_fetch_complete(len(all_jobs))
        return all_jobs

    def _resolve_countries(self, country: str) -> List[str]:
        """Resolve country option into a list of valid country codes."""
        if country.lower() == "all":
            return list(ADZUNA_COUNTRIES.keys())

        codes = [c.strip().lower() for c in country.split(",")]
        valid = [c for c in codes if c in ADZUNA_COUNTRIES]

        if not valid:
            logger.warning(f"[adzuna] No valid countries in '{country}', using all.")
            return list(ADZUNA_COUNTRIES.keys())

        return valid

    def _fetch_country(
        self,
        keywords: List[str],
        location: str,
        country: str,
        max_results: int,
    ) -> List[ScrapedJob]:
        """Fetch jobs from a single country."""
        jobs: List[ScrapedJob] = []
        query = " ".join(keywords)
        page = 1
        per_page = min(50, max_results)

        while len(jobs) < max_results:
            try:
                results = self._fetch_page(
                    query=query,
                    location=location,
                    country=country,
                    page=page,
                    per_page=per_page,
                )

                if not results:
                    break

                for result in results:
                    job = self._parse_result(result, country)
                    if job:
                        jobs.append(job)

                if len(results) < per_page:
                    break

                page += 1

            except Exception as e:
                logger.warning(f"[adzuna:{country}] Error on page {page}: {e}")
                break

        return jobs[:max_results]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
    )
    def _fetch_page(
        self,
        query: str,
        location: str,
        country: str,
        page: int,
        per_page: int,
    ) -> List[dict]:
        """Fetch a single page of results from Adzuna."""
        url = f"{self.BASE_URL}/{country}/search/{page}"

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": per_page,
            "what": query,
            "content-type": "application/json",
        }

        if location:
            params["where"] = location

        response = self.client.get(url, params=params)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            logger.warning(f"[adzuna:{country}] Rate limited, retry after {retry_after}s")
            raise httpx.HTTPStatusError(
                "Rate limited",
                request=response.request,
                response=response,
            )

        response.raise_for_status()
        data = response.json()

        return data.get("results", [])

    def _parse_result(self, result: dict, country: str) -> Optional[ScrapedJob]:
        """Parse an Adzuna API result into a ScrapedJob."""
        try:
            title = result.get("title", "").strip()
            description = result.get("description", "").strip()
            company_name = result.get("company", {}).get("display_name", "Unknown")

            if not title or not description:
                return None

            # Build location text
            location_data = result.get("location", {})
            location_text = location_data.get("display_name", "")

            # Use proper currency for this country
            currency = ADZUNA_COUNTRIES.get(country, {}).get("currency", "USD")

            salary_text = None
            salary_min = result.get("salary_min")
            salary_max = result.get("salary_max")
            if salary_min or salary_max:
                if salary_min and salary_max:
                    salary_text = f"{currency} {int(salary_min):,} - {int(salary_max):,}"
                elif salary_min:
                    salary_text = f"{currency} {int(salary_min):,}"
                elif salary_max:
                    salary_text = f"{currency} {int(salary_max):,}"

            # Parse posted date
            posted_at = None
            created = result.get("created")
            if created:
                try:
                    posted_at = datetime.fromisoformat(
                        created.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            # Determine employment type
            employment_type = "full_time"
            contract_type = result.get("contract_type", "")
            contract_time = result.get("contract_time", "")

            if contract_type == "contract":
                employment_type = "contract"
            elif contract_time == "part_time":
                employment_type = "part_time"

            return ScrapedJob(
                title=title,
                description=description,
                company=company_name,
                location=location_text,
                url=result.get("redirect_url"),
                source_job_id=f"adzuna_{result.get('id', '')}",
                apply_url=result.get("redirect_url"),
                salary_text=salary_text,
                employment_type=employment_type,
                posted_at=posted_at,
            )

        except Exception as e:
            logger.warning(f"[adzuna:{country}] Failed to parse result: {e}")
            return None

    def __del__(self):
        """Close the HTTP client."""
        try:
            self.client.close()
        except Exception:
            pass
