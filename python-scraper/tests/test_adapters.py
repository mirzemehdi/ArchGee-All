"""Tests for CareerJet and Jooble adapters."""

import httpx
import pytest
import respx

from adapters.careerjet import CareerJetAdapter
from adapters.jooble import JoobleAdapter


class TestCareerJetAdapter:
    """Test the CareerJet adapter."""

    def test_source_name(self):
        adapter = CareerJetAdapter(api_key="test")
        assert adapter.source_name == "careerjet"

    def test_no_credentials_returns_empty(self):
        adapter = CareerJetAdapter(api_key="")
        jobs = adapter.fetch_jobs(keywords=["architect"])
        assert jobs == []

    @respx.mock
    def test_parse_result(self):
        adapter = CareerJetAdapter(api_key="test")
        result = {
            "title": "Senior Architect",
            "description": "Design residential buildings.",
            "company": "Practice Ltd",
            "locations": "London, UK",
            "url": "https://careerjet.co.uk/job/123",
            "salary": "GBP 50,000 - 70,000",
        }
        job = adapter._parse_result(result)

        assert job is not None
        assert job.title == "Senior Architect"
        assert job.company == "Practice Ltd"
        assert job.location == "London, UK"
        assert job.salary_text == "GBP 50,000 - 70,000"

    @respx.mock
    def test_parse_result_missing_title_returns_none(self):
        adapter = CareerJetAdapter(api_key="test")
        result = {
            "title": "",
            "description": "Test",
            "company": "Test",
        }
        assert adapter._parse_result(result) is None

    @respx.mock
    def test_parse_result_missing_description_returns_none(self):
        adapter = CareerJetAdapter(api_key="test")
        result = {
            "title": "Architect",
            "description": "",
            "company": "Test",
        }
        assert adapter._parse_result(result) is None

    @respx.mock
    def test_fetch_jobs_success(self):
        response_data = {
            "jobs": [
                {
                    "title": "Architect",
                    "description": "Design buildings.",
                    "company": "Test Practice",
                    "locations": "London",
                    "url": "https://careerjet.co.uk/123",
                },
            ],
        }

        respx.get("https://search.api.careerjet.net/v4/query").mock(
            return_value=httpx.Response(200, json=response_data)
        )

        adapter = CareerJetAdapter(api_key="test_key")
        jobs = adapter.fetch_jobs(keywords=["architect"], max_results=10)

        assert len(jobs) == 1
        assert jobs[0].title == "Architect"

    @respx.mock
    def test_fetch_handles_error_gracefully(self):
        respx.get("https://search.api.careerjet.net/v4/query").mock(
            return_value=httpx.Response(500, text="Server Error")
        )

        adapter = CareerJetAdapter(api_key="test_key")
        jobs = adapter.fetch_jobs(keywords=["architect"])
        assert jobs == []


class TestJoobleAdapter:
    """Test the Jooble adapter."""

    def test_source_name(self):
        adapter = JoobleAdapter(api_key="test")
        assert adapter.source_name == "jooble"

    def test_no_credentials_returns_empty(self):
        adapter = JoobleAdapter(api_key="")
        jobs = adapter.fetch_jobs(keywords=["architect"])
        assert jobs == []

    def test_map_employment_type(self):
        assert JoobleAdapter._map_employment_type("full-time") == "full_time"
        assert JoobleAdapter._map_employment_type("part-time") == "part_time"
        assert JoobleAdapter._map_employment_type("contract") == "contract"
        assert JoobleAdapter._map_employment_type("temporary") == "contract"
        assert JoobleAdapter._map_employment_type("freelance") == "freelance"
        assert JoobleAdapter._map_employment_type("internship") == "internship"
        assert JoobleAdapter._map_employment_type("unknown") is None
        assert JoobleAdapter._map_employment_type("") is None

    @respx.mock
    def test_parse_result(self):
        adapter = JoobleAdapter(api_key="test")
        result = {
            "title": "Landscape Architect",
            "snippet": "Design public parks and gardens.",
            "company": "AECOM",
            "location": "Manchester, UK",
            "link": "https://jooble.org/job/123",
            "salary": "GBP 35,000 - 45,000",
            "type": "full-time",
            "updated": "2024-06-15T10:00:00Z",
        }
        job = adapter._parse_result(result)

        assert job is not None
        assert job.title == "Landscape Architect"
        assert job.description == "Design public parks and gardens."
        assert job.company == "AECOM"
        assert job.employment_type == "full_time"
        assert job.posted_at is not None

    @respx.mock
    def test_parse_result_missing_title_returns_none(self):
        adapter = JoobleAdapter(api_key="test")
        result = {"title": "", "snippet": "Test", "company": "Test"}
        assert adapter._parse_result(result) is None

    @respx.mock
    def test_parse_result_missing_snippet_returns_none(self):
        adapter = JoobleAdapter(api_key="test")
        result = {"title": "Architect", "snippet": "", "company": "Test"}
        assert adapter._parse_result(result) is None

    @respx.mock
    def test_fetch_jobs_success(self):
        response_data = {
            "jobs": [
                {
                    "title": "Urban Designer",
                    "snippet": "Master planning projects.",
                    "company": "MVRDV",
                    "location": "Rotterdam",
                    "link": "https://jooble.org/456",
                    "type": "full-time",
                },
            ],
        }
        empty_data = {"jobs": []}

        # First call returns results, second returns empty to stop pagination
        route = respx.post("https://jooble.org/api/test_key")
        route.side_effect = [
            httpx.Response(200, json=response_data),
            httpx.Response(200, json=empty_data),
        ]

        adapter = JoobleAdapter(api_key="test_key")
        jobs = adapter.fetch_jobs(keywords=["architect"], max_results=10)

        assert len(jobs) == 1
        assert jobs[0].title == "Urban Designer"
        assert jobs[0].employment_type == "full_time"

    @respx.mock
    def test_fetch_handles_error_gracefully(self):
        respx.post("https://jooble.org/api/test_key").mock(
            return_value=httpx.Response(500, text="Server Error")
        )

        adapter = JoobleAdapter(api_key="test_key")
        jobs = adapter.fetch_jobs(keywords=["architect"])
        assert jobs == []

    @respx.mock
    def test_fetch_empty_response(self):
        respx.post("https://jooble.org/api/test_key").mock(
            return_value=httpx.Response(200, json={"jobs": []})
        )

        adapter = JoobleAdapter(api_key="test_key")
        jobs = adapter.fetch_jobs(keywords=["architect"])
        assert jobs == []
