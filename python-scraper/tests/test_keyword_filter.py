"""Tests for the keyword filter that separates architecture from tech jobs."""

import pytest

from filters.keyword_filter import KeywordFilter, ARCHITECTURE_KEYWORDS, EXCLUDE_KEYWORDS
from models.job import ScrapedJob


def _make_job(title: str, description: str = "Generic job description.") -> ScrapedJob:
    """Helper to create a job with a given title and description."""
    return ScrapedJob(title=title, description=description, company="Test Co")


class TestKeywordFilterIsRelevant:
    """Test the is_relevant() method."""

    def test_architecture_title_passes(self):
        kf = KeywordFilter()
        job = _make_job("Senior Architect - Residential")
        assert kf.is_relevant(job) is True

    def test_interior_designer_title_passes(self):
        kf = KeywordFilter()
        job = _make_job("Interior Designer")
        assert kf.is_relevant(job) is True

    def test_landscape_architect_title_passes(self):
        kf = KeywordFilter()
        job = _make_job("Landscape Architect")
        assert kf.is_relevant(job) is True

    def test_bim_manager_title_passes(self):
        kf = KeywordFilter()
        job = _make_job("BIM Manager")
        assert kf.is_relevant(job) is True

    def test_revit_in_description_passes(self):
        kf = KeywordFilter()
        job = _make_job(
            "Design Technician",
            "Must have experience with Revit and AutoCAD.",
        )
        assert kf.is_relevant(job) is True

    def test_urban_planner_title_passes(self):
        kf = KeywordFilter()
        job = _make_job("Urban Planner - City Centre Redevelopment")
        assert kf.is_relevant(job) is True

    def test_riba_in_description_passes(self):
        kf = KeywordFilter()
        job = _make_job(
            "Part II Architectural Assistant",
            "RIBA Part II qualified preferred.",
        )
        assert kf.is_relevant(job) is True

    def test_software_architect_excluded(self):
        """Software architect should be filtered out."""
        kf = KeywordFilter()
        job = _make_job("Software Architect - Python/AWS")
        assert kf.is_relevant(job) is False

    def test_cloud_architect_excluded(self):
        kf = KeywordFilter()
        job = _make_job("Cloud Architect - Azure")
        assert kf.is_relevant(job) is False

    def test_solutions_architect_excluded(self):
        kf = KeywordFilter()
        job = _make_job("Solutions Architect - Enterprise")
        assert kf.is_relevant(job) is False

    def test_data_architect_excluded(self):
        kf = KeywordFilter()
        job = _make_job("Data Architect")
        assert kf.is_relevant(job) is False

    def test_devops_excluded(self):
        kf = KeywordFilter()
        job = _make_job("DevOps Engineer", "Kubernetes and Terraform experience required.")
        assert kf.is_relevant(job) is False

    def test_unrelated_job_excluded(self):
        """A completely unrelated job should not pass."""
        kf = KeywordFilter()
        job = _make_job("Marketing Manager", "Lead marketing campaigns for SaaS products.")
        assert kf.is_relevant(job) is False

    def test_case_insensitive_matching(self):
        """Keywords should match regardless of case."""
        kf = KeywordFilter()
        job = _make_job("SENIOR ARCHITECT")
        assert kf.is_relevant(job) is True

    def test_exclude_takes_priority_over_include(self):
        """If title matches both include and exclude, exclude wins."""
        kf = KeywordFilter()
        # 'enterprise architect' contains 'architect' (include) but matches
        # 'enterprise architect' (exclude) - exclude should win
        job = _make_job("Enterprise Architect - Digital Transformation")
        assert kf.is_relevant(job) is False

    def test_description_only_match_passes(self):
        """Job with architecture keyword only in description passes."""
        kf = KeywordFilter()
        job = _make_job(
            "Design Lead",
            "Working with architectural technologists on sustainable design projects.",
        )
        assert kf.is_relevant(job) is True

    def test_technical_architect_excluded(self):
        kf = KeywordFilter()
        job = _make_job("Technical Architect - Java")
        assert kf.is_relevant(job) is False


class TestKeywordFilterFilterJobs:
    """Test the filter_jobs() batch method."""

    def test_filters_batch_correctly(self):
        kf = KeywordFilter()
        jobs = [
            _make_job("Senior Architect"),
            _make_job("Software Architect - Python"),
            _make_job("Interior Designer"),
            _make_job("Cloud Architect"),
            _make_job("Landscape Architect"),
        ]
        filtered = kf.filter_jobs(jobs)
        assert len(filtered) == 3

        titles = {j.title for j in filtered}
        assert "Senior Architect" in titles
        assert "Interior Designer" in titles
        assert "Landscape Architect" in titles

    def test_empty_list_returns_empty(self):
        kf = KeywordFilter()
        assert kf.filter_jobs([]) == []

    def test_all_relevant_returns_all(self):
        kf = KeywordFilter()
        jobs = [
            _make_job("Architect"),
            _make_job("BIM Coordinator"),
        ]
        filtered = kf.filter_jobs(jobs)
        assert len(filtered) == 2

    def test_all_irrelevant_returns_empty(self):
        kf = KeywordFilter()
        jobs = [
            _make_job("Software Engineer"),
            _make_job("Product Manager"),
        ]
        filtered = kf.filter_jobs(jobs)
        assert len(filtered) == 0


class TestKeywordFilterCustomKeywords:
    """Test custom keyword lists."""

    def test_custom_include_keywords(self):
        kf = KeywordFilter(include_keywords=["custom_keyword"])
        job = _make_job("Custom_keyword Role")
        assert kf.is_relevant(job) is True

    def test_custom_exclude_keywords(self):
        kf = KeywordFilter(
            include_keywords=["architect"],
            exclude_keywords=["naval architect"],
        )
        job = _make_job("Naval Architect")
        assert kf.is_relevant(job) is False

    def test_default_keywords_are_populated(self):
        """Ensure the constants have reasonable keyword counts."""
        assert len(ARCHITECTURE_KEYWORDS) > 20
        assert len(EXCLUDE_KEYWORDS) > 10
