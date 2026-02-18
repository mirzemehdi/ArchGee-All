# ArchGee Python Scraper Guidelines

## Overview
The scraper microservice is a separate Python project that fetches jobs from various sources and POSTs them to the Laravel ingest API. Inspired by [JobSpy](https://github.com/speedyapply/JobSpy).

---

## Architecture

```
python-scraper/
├── main.py                  # CLI entry point / scheduler
├── config.py                # Configuration (env vars)
├── models/
│   └── job.py               # Job data model (Pydantic)
├── adapters/
│   ├── base.py              # Abstract adapter
│   ├── adzuna.py            # Adzuna API adapter
│   ├── careerjet.py         # CareerJet API adapter
│   ├── jooble.py            # Jooble API adapter
│   ├── linkedin.py          # LinkedIn Jobs (if API available)
│   └── indeed_scraper.py    # Web scraper (Phase 2)
├── client/
│   └── ingest_client.py     # HTTP client for Laravel API
├── filters/
│   └── keyword_filter.py    # Pre-filter by architecture keywords
├── utils/
│   ├── dedup.py             # Local deduplication cache
│   └── logger.py            # Structured logging
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Job Data Contract

Every adapter must produce jobs matching this Pydantic model:

```python
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class ScrapedJob(BaseModel):
    title: str
    description: str
    company: str
    company_website: Optional[str] = None
    location: str
    url: HttpUrl                        # Original job listing URL
    source_job_id: Optional[str] = None # Unique ID from the source
    apply_url: Optional[HttpUrl] = None
    salary_text: Optional[str] = None   # Raw salary string
    employment_type: Optional[str] = None
    posted_at: Optional[datetime] = None
```

---

## Adapter Pattern

```python
from abc import ABC, abstractmethod
from typing import List
from models.job import ScrapedJob

class BaseAdapter(ABC):
    """Base class for all job source adapters."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique source identifier (e.g., 'adzuna')."""
        pass

    @abstractmethod
    def fetch_jobs(self, keywords: List[str], location: str = "") -> List[ScrapedJob]:
        """Fetch jobs from the source. Must return ScrapedJob instances."""
        pass
```

---

## Ingest Client

```python
import httpx
from typing import List
from models.job import ScrapedJob

class IngestClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.client = httpx.Client(
            timeout=30.0,
            headers={"Authorization": f"Bearer {token}"}
        )

    def ingest_batch(self, source: str, jobs: List[ScrapedJob]) -> dict:
        """POST /api/ingest/jobs"""
        response = self.client.post(
            f"{self.base_url}/api/ingest/jobs",
            json={
                "source": source,
                "jobs": [job.model_dump(mode="json") for job in jobs]
            }
        )
        response.raise_for_status()
        return response.json()
```

---

## Keyword Filters

Pre-filter jobs before sending to Laravel (reduces API calls and AI processing costs):

```python
ARCHITECTURE_KEYWORDS = [
    "architect", "architecture", "architectural",
    "interior design", "interior designer",
    "landscape architect", "landscape design",
    "urban design", "urban planner", "urban planning",
    "BIM", "Revit", "AutoCAD", "ArchiCAD",
    "building design", "sustainable design",
    "heritage", "conservation architect",
    "masterplan", "town planner",
]

EXCLUDE_KEYWORDS = [
    "software architect", "cloud architect", "data architect",
    "solutions architect", "enterprise architect",
    "network architect", "security architect",
    "system architect", "IT architect",
]
```

A job passes the filter if:
1. Title OR description contains at least one `ARCHITECTURE_KEYWORDS` match
2. Title does NOT contain any `EXCLUDE_KEYWORDS` match

---

## Configuration

```env
# Laravel API
ARCHGEE_API_URL=https://archgee.com
ARCHGEE_API_TOKEN=your-sanctum-token

# Adzuna
ADZUNA_APP_ID=xxx
ADZUNA_APP_KEY=xxx

# CareerJet
CAREERJET_AFFID=xxx

# Jooble
JOOBLE_API_KEY=xxx

# Scheduling
FETCH_INTERVAL_HOURS=6
MAX_JOBS_PER_FETCH=100
```

---

## Scheduling

The scraper runs on a schedule (cron or task scheduler):

```
# Every 6 hours, fetch from all sources
0 */6 * * * cd /app && python main.py --all

# Specific source
python main.py --source adzuna --keywords "architect" --location "UK"
```

---

## Deduplication

Local deduplication before sending to Laravel:
1. Hash `title + company + location` → check against local SQLite/Redis cache
2. Include `source_job_id` so Laravel can also deduplicate server-side
3. Cache expiry: 30 days

---

## Error Handling

- Each adapter handles its own API errors and retries (3 attempts, exponential backoff)
- Failed jobs are logged but don't stop the batch
- HTTP 429 (rate limit) → respect `Retry-After` header
- Connection errors → retry with backoff, then skip source
- Send structured logs to stdout (for Docker log collection)

---

## Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py", "--all"]
```

---

## Testing

- Each adapter should have unit tests with mocked API responses
- Integration test: verify JSON output matches `ScrapedJob` schema
- End-to-end test: ingest into a local Laravel instance

---

## Phase 2 Additions
- Web scrapers for sites without APIs (use `httpx` + `beautifulsoup4`)
- Proxy rotation for web scraping
- Rate limiting per source
- Monitoring dashboard for scraper health
