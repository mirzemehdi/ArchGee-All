"""HTTP client for the Laravel ingest API."""

from __future__ import annotations

from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import config
from models.job import ScrapedJob
from utils.logger import get_logger

logger = get_logger(__name__)


class IngestClient:
    """Client for sending scraped jobs to the ArchGee Laravel ingest API."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
    ):
        self.base_url = (base_url or config.API_URL).rstrip("/")
        self.token = token or config.API_TOKEN
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    )
    def ingest_single(self, source: str, job: ScrapedJob) -> dict:
        """POST a single job to /api/ingest/job.

        Args:
            source: Source identifier (e.g., "adzuna").
            job: The scraped job to ingest.

        Returns:
            API response dict with id, status, duplicate fields.
        """
        payload = job.to_ingest_payload()
        payload["source"] = source

        response = self.client.post(
            f"{self.base_url}/api/ingest/job",
            json=payload,
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            logger.warning(f"Rate limited by API, retry after {retry_after}s")
            raise httpx.TimeoutException(f"Rate limited, retry after {retry_after}s")

        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    )
    def ingest_batch(self, source: str, jobs: List[ScrapedJob]) -> dict:
        """POST a batch of jobs to /api/ingest/jobs.

        Args:
            source: Source identifier.
            jobs: List of scraped jobs to ingest.

        Returns:
            API response dict with accepted, duplicates, errors counts.
        """
        payload = {
            "source": source,
            "jobs": [job.to_ingest_payload() for job in jobs],
        }

        response = self.client.post(
            f"{self.base_url}/api/ingest/jobs",
            json=payload,
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            logger.warning(f"Rate limited by API, retry after {retry_after}s")
            raise httpx.TimeoutException(f"Rate limited, retry after {retry_after}s")

        response.raise_for_status()
        return response.json()

    def ingest_in_batches(
        self, source: str, jobs: List[ScrapedJob], batch_size: int = 50
    ) -> dict:
        """Send jobs in batches to avoid timeouts and rate limits.

        Args:
            source: Source identifier.
            jobs: All jobs to ingest.
            batch_size: Jobs per API call (max 100).

        Returns:
            Combined results dict.
        """
        total_accepted = 0
        total_duplicates = 0
        total_errors = 0

        for i in range(0, len(jobs), batch_size):
            batch = jobs[i : i + batch_size]
            try:
                result = self.ingest_batch(source, batch)
                total_accepted += result.get("accepted", 0)
                total_duplicates += result.get("duplicates", 0)
                total_errors += result.get("errors", 0)

                logger.info(
                    f"Batch {i // batch_size + 1}: "
                    f"accepted={result.get('accepted', 0)}, "
                    f"duplicates={result.get('duplicates', 0)}, "
                    f"errors={result.get('errors', 0)}"
                )

            except Exception as e:
                logger.error(f"Batch {i // batch_size + 1} failed: {e}")
                total_errors += len(batch)

        return {
            "accepted": total_accepted,
            "duplicates": total_duplicates,
            "errors": total_errors,
        }

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass
