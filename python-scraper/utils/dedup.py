"""Local deduplication cache using SQLite.

Checks title + company + location hash against a local SQLite database
before sending jobs to the Laravel API, reducing unnecessary API calls.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path
from typing import List

from models.job import ScrapedJob
from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "dedup_cache.db"
CACHE_EXPIRY_DAYS = 30


class DedupCache:
    """Local deduplication cache backed by SQLite."""

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_jobs (
                    hash TEXT PRIMARY KEY,
                    source TEXT,
                    source_job_id TEXT,
                    title TEXT,
                    created_at INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON seen_jobs (created_at)
            """)
            conn.commit()

    @staticmethod
    def _hash_job(job: ScrapedJob) -> str:
        """Generate a hash for a job based on title + company + location."""
        key = f"{job.title.lower().strip()}|{job.company.lower().strip()}|{job.location.lower().strip()}"
        return hashlib.sha256(key.encode()).hexdigest()

    def is_seen(self, job: ScrapedJob) -> bool:
        """Check if a job has been seen before.

        Checks both by source_job_id (if available) and by content hash.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            # Check by source_job_id first
            if job.source_job_id:
                cursor = conn.execute(
                    "SELECT 1 FROM seen_jobs WHERE source_job_id = ?",
                    (job.source_job_id,),
                )
                if cursor.fetchone():
                    return True

            # Check by content hash
            job_hash = self._hash_job(job)
            cursor = conn.execute(
                "SELECT 1 FROM seen_jobs WHERE hash = ?",
                (job_hash,),
            )
            return cursor.fetchone() is not None

    def mark_seen(self, job: ScrapedJob, source: str) -> None:
        """Mark a job as seen in the cache."""
        job_hash = self._hash_job(job)
        now = int(time.time())

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO seen_jobs
                   (hash, source, source_job_id, title, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (job_hash, source, job.source_job_id, job.title, now),
            )
            conn.commit()

    def filter_new(self, jobs: List[ScrapedJob]) -> List[ScrapedJob]:
        """Filter out already-seen jobs.

        Args:
            jobs: List of scraped jobs.

        Returns:
            List of jobs not yet in the cache.
        """
        new_jobs = [job for job in jobs if not self.is_seen(job)]

        seen_count = len(jobs) - len(new_jobs)
        if seen_count > 0:
            logger.info(f"Dedup cache: {seen_count} duplicates filtered out")

        return new_jobs

    def mark_batch_seen(self, jobs: List[ScrapedJob], source: str) -> None:
        """Mark multiple jobs as seen."""
        for job in jobs:
            self.mark_seen(job, source)

    def cleanup_expired(self) -> int:
        """Remove entries older than CACHE_EXPIRY_DAYS.

        Returns:
            Number of entries removed.
        """
        cutoff = int(time.time()) - (CACHE_EXPIRY_DAYS * 86400)

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "DELETE FROM seen_jobs WHERE created_at < ?",
                (cutoff,),
            )
            conn.commit()
            removed = cursor.rowcount

        if removed > 0:
            logger.info(f"Dedup cache cleanup: {removed} expired entries removed")

        return removed

    def count(self) -> int:
        """Get the number of entries in the cache."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM seen_jobs")
            return cursor.fetchone()[0]
