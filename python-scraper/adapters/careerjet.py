"""CareerJet API adapter for fetching architecture jobs.

CareerJet provides a search API authenticated via Basic HTTP auth.
Docs: https://www.careerjet.com/partners/api/
"""

import socket
import time
from typing import List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from adapters.base import BaseAdapter
from config import config
from models.job import ScrapedJob
from utils.logger import get_logger

logger = get_logger(__name__)

MAX_PAGE = 10
MAX_PAGE_SIZE = 100
REQUEST_DELAY_SECONDS = 0.5


class CareerJetAdapter(BaseAdapter):
    """Fetches architecture jobs from the CareerJet API.

    CareerJet provides a job search API authenticated via Basic HTTP auth
    using the API key as the username and an empty password.
    Docs: https://www.careerjet.com/partners/api/
    """

    BASE_URL = "https://search.api.careerjet.net/v4/query"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.CAREERJET_API_KEY
        self.client = httpx.Client(
            timeout=30.0,
            auth=(self.api_key, "") if self.api_key else None,
        )

    @property
    def source_name(self) -> str:
        return "careerjet"

    def fetch_jobs(
        self,
        keywords: List[str],
        location: str = "",
        max_results: int = 100,
    ) -> List[ScrapedJob]:
        """Fetch jobs from CareerJet API."""
        if not self.api_key:
            logger.warning("[careerjet] No API key configured, skipping.")
            return []

        self._log_fetch_start(keywords, location)

        all_jobs: List[ScrapedJob] = []
        query = " ".join(keywords)
        page = 1
        per_page = min(MAX_PAGE_SIZE, max_results)

        while len(all_jobs) < max_results and page <= MAX_PAGE:
            try:
                results = self._fetch_page(query, location, page, per_page)

                if not results:
                    break

                for result in results:
                    job = self._parse_result(result)
                    if job:
                        all_jobs.append(job)

                if len(results) < per_page:
                    break

                page += 1
                time.sleep(REQUEST_DELAY_SECONDS)

            except Exception as e:
                self._log_fetch_error(e)
                break

        self._log_fetch_complete(len(all_jobs))
        return all_jobs[:max_results]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
    )
    def _fetch_page(
        self, query: str, location: str, page: int, per_page: int
    ) -> List[dict]:
        """Fetch a single page of results from CareerJet."""
        params = {
            "keywords": query,
            "page": page,
            "page_size": per_page,
            "sort": "date",
            "user_ip": self._get_server_ip(),
            "user_agent": "ArchGee Job Scraper/1.0 (https://archgee.com)",
            "locale_code": "en_GB",
        }

        if location:
            params["location"] = location

        response = self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        return data.get("jobs", [])

    def _parse_result(self, result: dict) -> Optional[ScrapedJob]:
        """Parse a CareerJet result into a ScrapedJob."""
        try:
            title = result.get("title", "").strip()
            description = result.get("description", "").strip()
            company = result.get("company", "Unknown").strip()

            if not title or not description:
                return None

            return ScrapedJob(
                title=title,
                description=description,
                company=company,
                location=result.get("locations", ""),
                url=result.get("url"),
                apply_url=result.get("url"),
                salary_text=result.get("salary"),
                posted_at=None,
            )

        except Exception as e:
            logger.warning(f"[careerjet] Failed to parse result: {e}")
            return None

    @staticmethod
    def _get_server_ip() -> str:
        """Get the server's outbound IP address."""
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return "127.0.0.1"

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass
