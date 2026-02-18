"""Tests for the ScrapedJob Pydantic model."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models.job import ScrapedJob


class TestScrapedJobCreation:
    """Test creating ScrapedJob instances."""

    def test_create_minimal_job(self):
        """Minimum required fields: title, description, company."""
        job = ScrapedJob(
            title="Architect",
            description="Design buildings.",
            company="ACME Ltd",
        )
        assert job.title == "Architect"
        assert job.description == "Design buildings."
        assert job.company == "ACME Ltd"
        assert job.location == ""
        assert job.url is None
        assert job.source_job_id is None
        assert job.employment_type is None

    def test_create_full_job(self, sample_job):
        """All fields populated."""
        assert sample_job.title == "Senior Architect"
        assert sample_job.company == "Foster & Partners"
        assert sample_job.location == "London, UK"
        assert sample_job.salary_text == "GBP 55,000 - 75,000"
        assert sample_job.employment_type == "full_time"
        assert sample_job.posted_at is not None
        assert sample_job.source_job_id == "adzuna_123"

    def test_strips_whitespace_from_required_fields(self):
        """Validator should strip leading/trailing whitespace."""
        job = ScrapedJob(
            title="  Senior Architect  ",
            description="  Design buildings.  ",
            company="  ACME Ltd  ",
        )
        assert job.title == "Senior Architect"
        assert job.description == "Design buildings."
        assert job.company == "ACME Ltd"


class TestScrapedJobValidation:
    """Test field validation rules."""

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            ScrapedJob(title="", description="Test", company="Test")

    def test_whitespace_title_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            ScrapedJob(title="   ", description="Test", company="Test")

    def test_empty_description_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            ScrapedJob(title="Architect", description="", company="Test")

    def test_empty_company_raises(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            ScrapedJob(title="Architect", description="Test", company="")

    def test_valid_employment_types(self):
        valid_types = ["full_time", "part_time", "contract", "freelance", "internship"]
        for emp_type in valid_types:
            job = ScrapedJob(
                title="Architect",
                description="Test",
                company="Test",
                employment_type=emp_type,
            )
            assert job.employment_type == emp_type

    def test_invalid_employment_type_defaults_to_full_time(self):
        """Unknown employment types should default to full_time."""
        job = ScrapedJob(
            title="Architect",
            description="Test",
            company="Test",
            employment_type="unknown_type",
        )
        assert job.employment_type == "full_time"

    def test_none_employment_type_stays_none(self):
        job = ScrapedJob(
            title="Architect",
            description="Test",
            company="Test",
            employment_type=None,
        )
        assert job.employment_type is None


class TestToIngestPayload:
    """Test the to_ingest_payload() method."""

    def test_minimal_payload_has_required_fields(self):
        job = ScrapedJob(
            title="Architect",
            description="Design buildings.",
            company="ACME Ltd",
        )
        payload = job.to_ingest_payload()

        assert payload["title"] == "Architect"
        assert payload["description"] == "Design buildings."
        assert payload["company"] == "ACME Ltd"
        assert payload["location"] == ""
        assert "url" not in payload
        assert "source_job_id" not in payload
        assert "salary_text" not in payload

    def test_full_payload_includes_all_fields(self, sample_job):
        payload = sample_job.to_ingest_payload()

        assert payload["title"] == "Senior Architect"
        assert payload["company"] == "Foster & Partners"
        assert payload["location"] == "London, UK"
        assert payload["url"] == "https://example.com/jobs/123"
        assert payload["source_job_id"] == "adzuna_123"
        assert payload["apply_url"] == "https://example.com/apply/123"
        assert payload["salary_text"] == "GBP 55,000 - 75,000"
        assert payload["employment_type"] == "full_time"
        assert "posted_at" in payload

    def test_posted_at_is_isoformat(self, sample_job):
        payload = sample_job.to_ingest_payload()
        # Should be parseable ISO format
        parsed = datetime.fromisoformat(payload["posted_at"])
        assert parsed.year == 2024
        assert parsed.month == 6

    def test_optional_none_fields_excluded(self):
        """Fields that are None should not appear in payload."""
        job = ScrapedJob(
            title="Architect",
            description="Design buildings.",
            company="ACME Ltd",
            url=None,
            salary_text=None,
            employment_type=None,
        )
        payload = job.to_ingest_payload()

        assert "url" not in payload
        assert "salary_text" not in payload
        assert "employment_type" not in payload
        assert "company_website" not in payload

    def test_company_website_included_when_set(self):
        job = ScrapedJob(
            title="Architect",
            description="Test",
            company="Test",
            company_website="https://company.com",
        )
        payload = job.to_ingest_payload()
        assert payload["company_website"] == "https://company.com"
