"""Tests for the SQLite deduplication cache."""

from __future__ import annotations

import time

import pytest

from models.job import ScrapedJob
from utils.dedup import DedupCache, CACHE_EXPIRY_DAYS


def _make_job(
    title: str = "Architect",
    company: str = "ACME",
    location: str = "London",
    source_job_id: str | None = None,
) -> ScrapedJob:
    return ScrapedJob(
        title=title,
        description="Test job description.",
        company=company,
        location=location,
        source_job_id=source_job_id,
    )


class TestDedupCacheInit:
    """Test cache initialization."""

    def test_creates_db_file(self, tmp_path):
        db_path = tmp_path / "subdir" / "test.db"
        cache = DedupCache(db_path=db_path)
        assert db_path.exists()

    def test_fresh_cache_has_zero_count(self, temp_dedup_cache):
        assert temp_dedup_cache.count() == 0


class TestIsSeen:
    """Test duplicate detection."""

    def test_new_job_is_not_seen(self, temp_dedup_cache):
        job = _make_job()
        assert temp_dedup_cache.is_seen(job) is False

    def test_marked_job_is_seen(self, temp_dedup_cache):
        job = _make_job(source_job_id="adzuna_100")
        temp_dedup_cache.mark_seen(job, "adzuna")
        assert temp_dedup_cache.is_seen(job) is True

    def test_seen_by_source_job_id(self, temp_dedup_cache):
        """Jobs with the same source_job_id should be detected even with different content."""
        job1 = _make_job(title="Architect v1", source_job_id="adzuna_200")
        temp_dedup_cache.mark_seen(job1, "adzuna")

        # Same source_job_id but different title
        job2 = _make_job(title="Architect v2", source_job_id="adzuna_200")
        assert temp_dedup_cache.is_seen(job2) is True

    def test_seen_by_content_hash(self, temp_dedup_cache):
        """Jobs with same title+company+location but different source_job_id should be detected."""
        job1 = _make_job(title="Senior Architect", company="Studio", location="NYC", source_job_id="src_1")
        temp_dedup_cache.mark_seen(job1, "adzuna")

        # Same content, different source_job_id
        job2 = _make_job(title="Senior Architect", company="Studio", location="NYC", source_job_id="src_999")
        assert temp_dedup_cache.is_seen(job2) is True

    def test_case_insensitive_hash(self, temp_dedup_cache):
        """Hash should be case-insensitive for title, company, location."""
        job1 = _make_job(title="Senior Architect", company="ACME", location="London")
        temp_dedup_cache.mark_seen(job1, "adzuna")

        job2 = _make_job(title="senior architect", company="acme", location="london")
        assert temp_dedup_cache.is_seen(job2) is True

    def test_different_jobs_not_confused(self, temp_dedup_cache):
        job1 = _make_job(title="Architect", company="Company A", location="London")
        temp_dedup_cache.mark_seen(job1, "adzuna")

        job2 = _make_job(title="Architect", company="Company B", location="London")
        assert temp_dedup_cache.is_seen(job2) is False


class TestFilterNew:
    """Test bulk filtering of new vs. seen jobs."""

    def test_all_new_jobs_pass(self, temp_dedup_cache):
        jobs = [_make_job(source_job_id=f"id_{i}") for i in range(5)]
        new = temp_dedup_cache.filter_new(jobs)
        assert len(new) == 5

    def test_all_seen_jobs_filtered(self, temp_dedup_cache):
        jobs = [_make_job(title=f"Job {i}", source_job_id=f"id_{i}") for i in range(3)]
        temp_dedup_cache.mark_batch_seen(jobs, "adzuna")

        new = temp_dedup_cache.filter_new(jobs)
        assert len(new) == 0

    def test_mix_of_new_and_seen(self, temp_dedup_cache):
        seen_job = _make_job(title="Old Job", source_job_id="old_1")
        temp_dedup_cache.mark_seen(seen_job, "adzuna")

        jobs = [
            seen_job,
            _make_job(title="New Job 1", source_job_id="new_1"),
            _make_job(title="New Job 2", source_job_id="new_2"),
        ]
        new = temp_dedup_cache.filter_new(jobs)
        assert len(new) == 2

    def test_empty_list_returns_empty(self, temp_dedup_cache):
        assert temp_dedup_cache.filter_new([]) == []


class TestMarkBatchSeen:
    """Test marking multiple jobs as seen."""

    def test_batch_mark_increments_count(self, temp_dedup_cache):
        jobs = [_make_job(title=f"Job {i}", source_job_id=f"batch_{i}") for i in range(5)]
        temp_dedup_cache.mark_batch_seen(jobs, "adzuna")
        assert temp_dedup_cache.count() == 5

    def test_batch_mark_all_become_seen(self, temp_dedup_cache):
        jobs = [_make_job(title=f"Job {i}", source_job_id=f"batch_{i}") for i in range(3)]
        temp_dedup_cache.mark_batch_seen(jobs, "adzuna")
        for job in jobs:
            assert temp_dedup_cache.is_seen(job) is True


class TestCleanupExpired:
    """Test cache expiry cleanup."""

    def test_cleanup_removes_old_entries(self, tmp_path):
        import sqlite3

        db_path = tmp_path / "expire_test.db"
        cache = DedupCache(db_path=db_path)

        # Insert a job normally
        job = _make_job(source_job_id="recent")
        cache.mark_seen(job, "adzuna")

        # Manually insert an old entry (31 days ago)
        old_ts = int(time.time()) - (31 * 86400)
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute(
                "INSERT INTO seen_jobs (hash, source, source_job_id, title, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                ("oldhash123", "adzuna", "old_job", "Old Job", old_ts),
            )
            conn.commit()

        assert cache.count() == 2
        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.count() == 1

    def test_cleanup_keeps_fresh_entries(self, temp_dedup_cache):
        jobs = [_make_job(title=f"Fresh {i}", source_job_id=f"fresh_{i}") for i in range(3)]
        temp_dedup_cache.mark_batch_seen(jobs, "adzuna")

        removed = temp_dedup_cache.cleanup_expired()
        assert removed == 0
        assert temp_dedup_cache.count() == 3

    def test_cleanup_on_empty_cache(self, temp_dedup_cache):
        removed = temp_dedup_cache.cleanup_expired()
        assert removed == 0
