"""Tests for the Adzuna API adapter."""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import httpx
import pytest
import respx

from adapters.adzuna import AdzunaAdapter, ADZUNA_COUNTRIES


class TestResolveCountries:
    """Test country code resolution."""

    def test_all_returns_all_countries(self):
        adapter = AdzunaAdapter(app_id="test", app_key="test")
        countries = adapter._resolve_countries("all")
        assert len(countries) == len(ADZUNA_COUNTRIES)
        assert "gb" in countries
        assert "us" in countries
        assert "de" in countries

    def test_single_country(self):
        adapter = AdzunaAdapter(app_id="test", app_key="test")
        countries = adapter._resolve_countries("gb")
        assert countries == ["gb"]

    def test_comma_separated_countries(self):
        adapter = AdzunaAdapter(app_id="test", app_key="test")
        countries = adapter._resolve_countries("gb,us,de")
        assert set(countries) == {"gb", "us", "de"}

    def test_invalid_country_filtered_out(self):
        adapter = AdzunaAdapter(app_id="test", app_key="test")
        countries = adapter._resolve_countries("gb,xx,us")
        assert set(countries) == {"gb", "us"}

    def test_all_invalid_falls_back_to_all(self):
        adapter = AdzunaAdapter(app_id="test", app_key="test")
        countries = adapter._resolve_countries("xx,yy,zz")
        assert len(countries) == len(ADZUNA_COUNTRIES)

    def test_case_insensitive(self):
        adapter = AdzunaAdapter(app_id="test", app_key="test")
        countries = adapter._resolve_countries("GB,US")
        assert set(countries) == {"gb", "us"}

    def test_whitespace_handling(self):
        adapter = AdzunaAdapter(app_id="test", app_key="test")
        countries = adapter._resolve_countries(" gb , us , de ")
        assert set(countries) == {"gb", "us", "de"}


class TestAdzunaCountriesConfig:
    """Test the countries configuration."""

    def test_all_countries_have_name(self):
        for code, info in ADZUNA_COUNTRIES.items():
            assert "name" in info, f"Country {code} missing name"
            assert len(info["name"]) > 0

    def test_all_countries_have_currency(self):
        for code, info in ADZUNA_COUNTRIES.items():
            assert "currency" in info, f"Country {code} missing currency"
            assert len(info["currency"]) == 3  # ISO currency codes are 3 chars

    def test_expected_countries_present(self):
        expected = ["gb", "us", "au", "ca", "de", "fr", "in", "nl", "nz", "sg", "za", "at", "br", "it", "pl"]
        for code in expected:
            assert code in ADZUNA_COUNTRIES, f"Expected country {code} not found"

    def test_15_countries_configured(self):
        assert len(ADZUNA_COUNTRIES) == 15


class TestParseResult:
    """Test parsing Adzuna API results into ScrapedJob."""

    def _make_adapter(self):
        return AdzunaAdapter(app_id="test", app_key="test")

    def test_parse_full_result(self, adzuna_api_response):
        adapter = self._make_adapter()
        result = adzuna_api_response["results"][0]
        job = adapter._parse_result(result, "gb")

        assert job is not None
        assert job.title == "Senior Architect"
        assert job.company == "Foster & Partners"
        assert job.location == "London, Greater London"
        assert job.source_job_id == "adzuna_4001234567"
        assert "GBP" in job.salary_text
        assert "55,000" in job.salary_text
        assert "75,000" in job.salary_text
        assert job.employment_type == "full_time"

    def test_parse_contract_type(self, adzuna_api_response):
        adapter = self._make_adapter()
        result = adzuna_api_response["results"][1]  # contract type
        job = adapter._parse_result(result, "gb")

        assert job is not None
        assert job.employment_type == "contract"

    def test_parse_part_time(self, adzuna_api_response):
        adapter = self._make_adapter()
        result = adzuna_api_response["results"][2]  # part_time
        job = adapter._parse_result(result, "gb")

        assert job is not None
        assert job.employment_type == "part_time"

    def test_parse_uses_correct_currency_per_country(self):
        adapter = self._make_adapter()
        result = {
            "id": "999",
            "title": "Architect",
            "description": "Design buildings.",
            "company": {"display_name": "Test GmbH"},
            "location": {"display_name": "Berlin"},
            "redirect_url": "https://example.com/999",
            "salary_min": 50000,
            "salary_max": 70000,
            "contract_type": "",
            "contract_time": "full_time",
            "created": "2024-06-15T10:00:00Z",
        }

        # Test German job uses EUR
        job_de = adapter._parse_result(result, "de")
        assert "EUR" in job_de.salary_text

        # Test US job uses USD
        job_us = adapter._parse_result(result, "us")
        assert "USD" in job_us.salary_text

        # Test Australian job uses AUD
        job_au = adapter._parse_result(result, "au")
        assert "AUD" in job_au.salary_text

    def test_parse_result_without_salary(self):
        adapter = self._make_adapter()
        result = {
            "id": "888",
            "title": "Junior Architect",
            "description": "Entry level position.",
            "company": {"display_name": "Small Practice"},
            "location": {"display_name": "Bristol"},
            "redirect_url": "https://example.com/888",
            "salary_min": None,
            "salary_max": None,
            "created": "2024-06-10T10:00:00Z",
        }
        job = adapter._parse_result(result, "gb")
        assert job is not None
        assert job.salary_text is None

    def test_parse_result_salary_min_only(self):
        adapter = self._make_adapter()
        result = {
            "id": "777",
            "title": "Architect",
            "description": "Test.",
            "company": {"display_name": "Test"},
            "location": {"display_name": "London"},
            "redirect_url": "https://example.com/777",
            "salary_min": 40000,
            "salary_max": None,
            "created": "2024-06-10T10:00:00Z",
        }
        job = adapter._parse_result(result, "gb")
        assert job.salary_text == "GBP 40,000"

    def test_parse_result_missing_title_returns_none(self):
        adapter = self._make_adapter()
        result = {
            "id": "666",
            "title": "",
            "description": "Description",
            "company": {"display_name": "Test"},
            "location": {"display_name": "London"},
        }
        job = adapter._parse_result(result, "gb")
        assert job is None

    def test_parse_result_missing_description_returns_none(self):
        adapter = self._make_adapter()
        result = {
            "id": "555",
            "title": "Architect",
            "description": "",
            "company": {"display_name": "Test"},
            "location": {"display_name": "London"},
        }
        job = adapter._parse_result(result, "gb")
        assert job is None

    def test_parse_posted_date(self, adzuna_api_response):
        adapter = self._make_adapter()
        result = adzuna_api_response["results"][0]
        job = adapter._parse_result(result, "gb")

        assert job.posted_at is not None
        assert job.posted_at.year == 2024
        assert job.posted_at.month == 6
        assert job.posted_at.day == 15


class TestFetchJobs:
    """Test the full fetch_jobs method with mocked HTTP."""

    @respx.mock
    def test_fetch_jobs_no_credentials_returns_empty(self):
        adapter = AdzunaAdapter(app_id="", app_key="")
        jobs = adapter.fetch_jobs(keywords=["architect"], country="gb")
        assert jobs == []

    @respx.mock
    def test_fetch_single_country(self, adzuna_api_response):
        route = respx.get("https://api.adzuna.com/v1/api/jobs/gb/search/1").mock(
            return_value=httpx.Response(200, json=adzuna_api_response)
        )

        adapter = AdzunaAdapter(app_id="test_id", app_key="test_key")
        jobs = adapter.fetch_jobs(keywords=["architect"], country="gb", max_results=10)

        assert len(jobs) == 3
        assert route.called

    @respx.mock
    def test_fetch_handles_empty_response(self, adzuna_empty_response):
        respx.get("https://api.adzuna.com/v1/api/jobs/gb/search/1").mock(
            return_value=httpx.Response(200, json=adzuna_empty_response)
        )

        adapter = AdzunaAdapter(app_id="test_id", app_key="test_key")
        jobs = adapter.fetch_jobs(keywords=["architect"], country="gb")
        assert jobs == []

    @respx.mock
    def test_fetch_multiple_countries(self, adzuna_api_response, adzuna_empty_response):
        # GB returns results, US returns empty
        respx.get("https://api.adzuna.com/v1/api/jobs/gb/search/1").mock(
            return_value=httpx.Response(200, json=adzuna_api_response)
        )
        respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
            return_value=httpx.Response(200, json=adzuna_empty_response)
        )

        adapter = AdzunaAdapter(app_id="test_id", app_key="test_key")
        jobs = adapter.fetch_jobs(keywords=["architect"], country="gb,us", max_results=50)

        assert len(jobs) == 3  # Only from GB

    @respx.mock
    def test_fetch_handles_api_error_gracefully(self):
        respx.get("https://api.adzuna.com/v1/api/jobs/gb/search/1").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        adapter = AdzunaAdapter(app_id="test_id", app_key="test_key")
        # Should not raise, just return empty
        jobs = adapter.fetch_jobs(keywords=["architect"], country="gb")
        assert jobs == []

    @respx.mock
    def test_fetch_pagination_stops_at_max_results(self):
        page1 = {
            "results": [
                {
                    "id": str(i),
                    "title": f"Architect {i}",
                    "description": "Design buildings.",
                    "company": {"display_name": "Company"},
                    "location": {"display_name": "London"},
                    "redirect_url": f"https://example.com/{i}",
                    "created": "2024-06-15T10:00:00Z",
                }
                for i in range(5)
            ],
            "count": 5,
        }

        respx.get("https://api.adzuna.com/v1/api/jobs/gb/search/1").mock(
            return_value=httpx.Response(200, json=page1)
        )

        adapter = AdzunaAdapter(app_id="test_id", app_key="test_key")
        jobs = adapter.fetch_jobs(keywords=["architect"], country="gb", max_results=3)

        assert len(jobs) == 3
