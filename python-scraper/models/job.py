"""Pydantic model for scraped job data."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator


class ScrapedJob(BaseModel):
    """Represents a job scraped from an external source.

    Every adapter must produce jobs matching this model before
    sending them to the Laravel ingest API.
    """

    title: str
    description: str
    company: str
    company_website: Optional[str] = None
    location: str = ""
    url: Optional[str] = None  # Original job listing URL
    source_job_id: Optional[str] = None  # Unique ID from the source
    apply_url: Optional[str] = None
    salary_text: Optional[str] = None  # Raw salary string
    employment_type: Optional[str] = None
    posted_at: Optional[datetime] = None

    @field_validator("title", "description", "company")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        valid = {"full_time", "part_time", "contract", "freelance", "internship"}
        if v not in valid:
            return "full_time"
        return v

    def to_ingest_payload(self) -> dict:
        """Convert to the format expected by the Laravel ingest API."""
        payload = {
            "title": self.title,
            "description": self.description,
            "company": self.company,
            "location": self.location,
        }

        if self.company_website:
            payload["company_website"] = self.company_website
        if self.url:
            payload["url"] = str(self.url)
        if self.source_job_id:
            payload["source_job_id"] = self.source_job_id
        if self.apply_url:
            payload["apply_url"] = str(self.apply_url)
        if self.salary_text:
            payload["salary_text"] = self.salary_text
        if self.employment_type:
            payload["employment_type"] = self.employment_type
        if self.posted_at:
            payload["posted_at"] = self.posted_at.isoformat()

        return payload
