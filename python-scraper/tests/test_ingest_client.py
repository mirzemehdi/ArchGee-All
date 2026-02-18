"""Tests for the Laravel ingest API client."""

import httpx
import pytest
import respx

from client.ingest_client import IngestClient
from models.job import ScrapedJob


def _make_job(title: str = "Architect", source_job_id: str = "test_1") -> ScrapedJob:
    return ScrapedJob(
        title=title,
        description="Design buildings.",
        company="Test Practice",
        location="London",
        source_job_id=source_job_id,
    )


class TestIngestSingle:
    """Test single job ingestion."""

    @respx.mock
    def test_ingest_single_success(self):
        route = respx.post("https://api.test.com/api/ingest/job").mock(
            return_value=httpx.Response(
                201,
                json={"id": "uuid-123", "status": "pending", "duplicate": False},
            )
        )

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        job = _make_job()
        result = client.ingest_single("adzuna", job)

        assert result["id"] == "uuid-123"
        assert result["status"] == "pending"
        assert result["duplicate"] is False
        assert route.called

    @respx.mock
    def test_ingest_single_sends_correct_payload(self):
        route = respx.post("https://api.test.com/api/ingest/job").mock(
            return_value=httpx.Response(201, json={"id": "uuid-123"})
        )

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        job = _make_job(title="Senior Architect", source_job_id="adzuna_999")
        client.ingest_single("adzuna", job)

        request = route.calls[0].request
        import json
        body = json.loads(request.content)
        assert body["title"] == "Senior Architect"
        assert body["source"] == "adzuna"
        assert body["source_job_id"] == "adzuna_999"

    @respx.mock
    def test_ingest_single_sends_auth_header(self):
        route = respx.post("https://api.test.com/api/ingest/job").mock(
            return_value=httpx.Response(201, json={"id": "uuid-123"})
        )

        client = IngestClient(base_url="https://api.test.com", token="my-secret-token")
        client.ingest_single("adzuna", _make_job())

        request = route.calls[0].request
        assert "Bearer my-secret-token" in request.headers["authorization"]

    @respx.mock
    def test_ingest_single_raises_on_server_error(self):
        respx.post("https://api.test.com/api/ingest/job").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        with pytest.raises(httpx.HTTPStatusError):
            client.ingest_single("adzuna", _make_job())


class TestIngestBatch:
    """Test batch job ingestion."""

    @respx.mock
    def test_ingest_batch_success(self):
        route = respx.post("https://api.test.com/api/ingest/jobs").mock(
            return_value=httpx.Response(
                200,
                json={"accepted": 3, "duplicates": 0, "errors": 0},
            )
        )

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        jobs = [_make_job(title=f"Job {i}", source_job_id=f"id_{i}") for i in range(3)]
        result = client.ingest_batch("adzuna", jobs)

        assert result["accepted"] == 3
        assert result["duplicates"] == 0
        assert route.called

    @respx.mock
    def test_ingest_batch_sends_jobs_array(self):
        route = respx.post("https://api.test.com/api/ingest/jobs").mock(
            return_value=httpx.Response(200, json={"accepted": 2})
        )

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        jobs = [_make_job(title=f"Job {i}", source_job_id=f"id_{i}") for i in range(2)]
        client.ingest_batch("adzuna", jobs)

        import json
        body = json.loads(route.calls[0].request.content)
        assert body["source"] == "adzuna"
        assert len(body["jobs"]) == 2
        assert body["jobs"][0]["title"] == "Job 0"
        assert body["jobs"][1]["title"] == "Job 1"


class TestIngestInBatches:
    """Test the batched ingestion with chunking."""

    @respx.mock
    def test_single_batch_when_under_limit(self):
        route = respx.post("https://api.test.com/api/ingest/jobs").mock(
            return_value=httpx.Response(
                200,
                json={"accepted": 5, "duplicates": 0, "errors": 0},
            )
        )

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        jobs = [_make_job(title=f"Job {i}", source_job_id=f"id_{i}") for i in range(5)]
        result = client.ingest_in_batches("adzuna", jobs, batch_size=50)

        assert result["accepted"] == 5
        assert route.call_count == 1

    @respx.mock
    def test_multiple_batches_when_over_limit(self):
        route = respx.post("https://api.test.com/api/ingest/jobs").mock(
            return_value=httpx.Response(
                200,
                json={"accepted": 2, "duplicates": 0, "errors": 0},
            )
        )

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        jobs = [_make_job(title=f"Job {i}", source_job_id=f"id_{i}") for i in range(5)]
        result = client.ingest_in_batches("adzuna", jobs, batch_size=2)

        # 5 jobs / batch_size 2 = 3 batches (2+2+1)
        assert route.call_count == 3
        assert result["accepted"] == 6  # 2 accepted per batch * 3 batches

    @respx.mock
    def test_batch_error_counted_correctly(self):
        # First batch succeeds, second fails
        route = respx.post("https://api.test.com/api/ingest/jobs")
        route.side_effect = [
            httpx.Response(200, json={"accepted": 2, "duplicates": 0, "errors": 0}),
            httpx.Response(500, text="Server Error"),
        ]

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        jobs = [_make_job(title=f"Job {i}", source_job_id=f"id_{i}") for i in range(4)]
        result = client.ingest_in_batches("adzuna", jobs, batch_size=2)

        assert result["accepted"] == 2
        assert result["errors"] == 2  # Second batch of 2 jobs all counted as errors

    @respx.mock
    def test_handles_duplicates_in_response(self):
        respx.post("https://api.test.com/api/ingest/jobs").mock(
            return_value=httpx.Response(
                200,
                json={"accepted": 1, "duplicates": 2, "errors": 0},
            )
        )

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        jobs = [_make_job(title=f"Job {i}", source_job_id=f"id_{i}") for i in range(3)]
        result = client.ingest_in_batches("adzuna", jobs, batch_size=50)

        assert result["accepted"] == 1
        assert result["duplicates"] == 2

    @respx.mock
    def test_empty_jobs_list(self):
        route = respx.post("https://api.test.com/api/ingest/jobs")

        client = IngestClient(base_url="https://api.test.com", token="test-token")
        result = client.ingest_in_batches("adzuna", [], batch_size=50)

        assert result["accepted"] == 0
        assert result["duplicates"] == 0
        assert result["errors"] == 0
        assert route.call_count == 0
