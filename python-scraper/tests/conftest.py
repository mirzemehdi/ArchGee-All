"""Shared fixtures for Python scraper tests."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from models.job import ScrapedJob
from utils.dedup import DedupCache


@pytest.fixture
def sample_job() -> ScrapedJob:
    """A typical architecture job for testing."""
    return ScrapedJob(
        title="Senior Architect",
        description="Design residential buildings for a leading practice.",
        company="Foster & Partners",
        location="London, UK",
        url="https://example.com/jobs/123",
        source_job_id="adzuna_123",
        apply_url="https://example.com/apply/123",
        salary_text="GBP 55,000 - 75,000",
        employment_type="full_time",
        posted_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_jobs() -> list[ScrapedJob]:
    """A list of diverse jobs for bulk testing."""
    return [
        ScrapedJob(
            title="Project Architect",
            description="Lead design on commercial projects.",
            company="Zaha Hadid Architects",
            location="London, UK",
            source_job_id="adzuna_1",
        ),
        ScrapedJob(
            title="Interior Designer",
            description="Residential interior design for high-end clients.",
            company="Studio Indigo",
            location="Paris, France",
            source_job_id="adzuna_2",
        ),
        ScrapedJob(
            title="Landscape Architect",
            description="Public parks and urban landscape design.",
            company="AECOM",
            location="New York, US",
            source_job_id="adzuna_3",
        ),
        ScrapedJob(
            title="BIM Manager",
            description="Manage BIM workflows using Revit and ArchiCAD.",
            company="Arup",
            location="Sydney, AU",
            source_job_id="adzuna_4",
        ),
        ScrapedJob(
            title="Urban Designer",
            description="Master planning and urban design projects.",
            company="MVRDV",
            location="Rotterdam, Netherlands",
            source_job_id="adzuna_5",
        ),
    ]


@pytest.fixture
def temp_dedup_cache(tmp_path) -> DedupCache:
    """A DedupCache using a temporary SQLite file."""
    db_path = tmp_path / "test_dedup.db"
    return DedupCache(db_path=db_path)


@pytest.fixture
def adzuna_api_response() -> dict:
    """A sample Adzuna API response with realistic data."""
    return {
        "results": [
            {
                "id": "4001234567",
                "title": "Senior Architect",
                "description": "We are looking for a Senior Architect to join our practice.",
                "company": {"display_name": "Foster & Partners"},
                "location": {"display_name": "London, Greater London"},
                "redirect_url": "https://www.adzuna.co.uk/jobs/detail/4001234567",
                "salary_min": 55000,
                "salary_max": 75000,
                "contract_type": "",
                "contract_time": "full_time",
                "created": "2024-06-15T10:00:00Z",
            },
            {
                "id": "4001234568",
                "title": "Interior Designer",
                "description": "Join our award-winning interior design studio.",
                "company": {"display_name": "Studio Indigo"},
                "location": {"display_name": "Chelsea, London"},
                "redirect_url": "https://www.adzuna.co.uk/jobs/detail/4001234568",
                "salary_min": None,
                "salary_max": None,
                "contract_type": "contract",
                "contract_time": "",
                "created": "2024-06-14T09:00:00Z",
            },
            {
                "id": "4001234569",
                "title": "Part-time BIM Coordinator",
                "description": "BIM coordination role, 3 days per week.",
                "company": {"display_name": "Arup"},
                "location": {"display_name": "Manchester"},
                "redirect_url": "https://www.adzuna.co.uk/jobs/detail/4001234569",
                "salary_min": 35000,
                "salary_max": None,
                "contract_type": "",
                "contract_time": "part_time",
                "created": "2024-06-13T08:30:00Z",
            },
        ],
        "count": 3,
    }


@pytest.fixture
def adzuna_empty_response() -> dict:
    """An empty Adzuna API response."""
    return {"results": [], "count": 0}
