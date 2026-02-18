"""CareerJet API adapter for fetching architecture jobs.

CareerJet provides an affiliate API. This is a placeholder adapter
that will be completed when CareerJet API credentials are available.
"""

from typing import List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from adapters.base import BaseAdapter
from config import config
from models.job import ScrapedJob
from utils.logger import get_logger

logger = get_logger(__name__)


class CareerJetAdapter(BaseAdapter):
    """Fetches architecture jobs from the CareerJet API.

    CareerJet provides a job search API accessible via affiliate ID.
    Docs: https://www.careerjet.com/partners/api/
    """

    BASE_URL = "http://public.api.careerjet.net/search"

    def __init__(self, affid: Optional[str] = None):
        self.affid = affid or config.CAREERJET_AFFID
        self.client = httpx.Client(timeout=30.0)

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
        if not self.affid:
            logger.warning("[careerjet] No affiliate ID configured, skipping.")
            return []

        self._log_fetch_start(keywords, location)

        all_jobs: List[ScrapedJob] = []
        query = " ".join(keywords)
        page = 1
        per_page = min(99, max_results)

        while len(all_jobs) < max_results:
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
            "affid": self.affid,
            "keywords": query,
            "page": page,
            "pagesize": per_page,
            "sort": "date",
            "user_ip": "0.0.0.0",
            "user_agent": "ArchGee Job Scraper/1.0",
            "url": "https://archgee.com",
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

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass
