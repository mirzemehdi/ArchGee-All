"""Jooble API adapter for fetching architecture jobs."""

from typing import List, Optional
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from adapters.base import BaseAdapter
from config import config
from models.job import ScrapedJob
from utils.logger import get_logger

logger = get_logger(__name__)


class JoobleAdapter(BaseAdapter):
    """Fetches architecture jobs from the Jooble API.

    Jooble provides a free job search API.
    Docs: https://jooble.org/api/about
    """

    BASE_URL = "https://jooble.org/api"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.JOOBLE_API_KEY
        self.client = httpx.Client(timeout=30.0)

    @property
    def source_name(self) -> str:
        return "jooble"

    def fetch_jobs(
        self,
        keywords: List[str],
        location: str = "",
        max_results: int = 100,
    ) -> List[ScrapedJob]:
        """Fetch jobs from Jooble API."""
        if not self.api_key:
            logger.warning("[jooble] No API key configured, skipping.")
            return []

        self._log_fetch_start(keywords, location)

        all_jobs: List[ScrapedJob] = []
        query = " ".join(keywords)
        page = 1

        while len(all_jobs) < max_results:
            try:
                results = self._fetch_page(query, location, page)

                if not results:
                    break

                for result in results:
                    job = self._parse_result(result)
                    if job:
                        all_jobs.append(job)

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
    def _fetch_page(self, query: str, location: str, page: int) -> List[dict]:
        """Fetch a page of results from Jooble."""
        url = f"{self.BASE_URL}/{self.api_key}"

        payload = {
            "keywords": query,
            "page": str(page),
        }

        if location:
            payload["location"] = location

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        return data.get("jobs", [])

    def _parse_result(self, result: dict) -> Optional[ScrapedJob]:
        """Parse a Jooble result into a ScrapedJob."""
        try:
            title = result.get("title", "").strip()
            snippet = result.get("snippet", "").strip()
            company = result.get("company", "Unknown").strip()

            if not title or not snippet:
                return None

            # Parse date
            posted_at = None
            updated = result.get("updated")
            if updated:
                try:
                    posted_at = datetime.fromisoformat(
                        updated.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            return ScrapedJob(
                title=title,
                description=snippet,
                company=company,
                location=result.get("location", ""),
                url=result.get("link"),
                apply_url=result.get("link"),
                salary_text=result.get("salary"),
                employment_type=self._map_employment_type(result.get("type", "")),
                posted_at=posted_at,
            )

        except Exception as e:
            logger.warning(f"[jooble] Failed to parse result: {e}")
            return None

    @staticmethod
    def _map_employment_type(job_type: str) -> Optional[str]:
        """Map Jooble job type to our employment type."""
        job_type = job_type.lower()
        mappings = {
            "full-time": "full_time",
            "part-time": "part_time",
            "contract": "contract",
            "temporary": "contract",
            "freelance": "freelance",
            "internship": "internship",
        }
        return mappings.get(job_type)

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass
