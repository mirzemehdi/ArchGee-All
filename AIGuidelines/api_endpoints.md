# ArchGee API Endpoints

## Overview
All APIs use JSON. Authentication via Laravel Sanctum (Bearer tokens).

---

## 1. Job Ingest API (Scraper/Aggregator Use)

### `POST /api/ingest/jobs`
Bulk ingest jobs from external sources.

**Auth**: `Bearer {SCRAPER_TOKEN}` (Sanctum token with `ingest:jobs` ability)

**Request Body**:
```json
{
  "source": "adzuna",
  "jobs": [
    {
      "title": "Senior Architect",
      "description": "Full job description text...",
      "company": "Foster + Partners",
      "company_website": "https://fosterandpartners.com",
      "location": "London, UK",
      "url": "https://original-listing.com/job/123",
      "source_job_id": "adzuna_12345",
      "apply_url": "https://apply.here.com/123",
      "salary_text": "£60,000 - £80,000",
      "employment_type": "full_time",
      "posted_at": "2026-01-15T00:00:00Z"
    }
  ]
}
```

**Response** `200 OK`:
```json
{
  "accepted": 5,
  "duplicates": 2,
  "errors": 0
}
```

**Rate Limit**: 100 requests/minute per token

---

### `POST /api/ingest/job`
Single job ingest (backwards-compatible).

**Auth**: `Bearer {SCRAPER_TOKEN}`

**Request Body**: Same as single item in the `jobs` array above.

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "status": "pending",
  "duplicate": false
}
```

---

## 2. Public REST API (Web/Mobile)

Base URL: `/api/v1`

### Jobs

#### `GET /api/v1/jobs`
List approved jobs with filters.

**Auth**: Optional (Sanctum for saved-job indicators)

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| q | string | Keyword search (title + description) |
| category | string | Category slug |
| location | string | Location text search |
| country | string | ISO country code |
| remote | string | `remote`, `hybrid`, `onsite` |
| seniority | string | `intern`, `junior`, `mid`, `senior`, `lead`, `principal`, `director` |
| employment_type | string | `full_time`, `part_time`, `contract`, `freelance`, `internship` |
| salary_min | int | Minimum annual salary |
| salary_max | int | Maximum annual salary |
| salary_currency | string | ISO 4217 currency code |
| sort | string | `latest` (default), `salary_desc`, `salary_asc`, `relevance` |
| page | int | Page number (default 1) |
| per_page | int | Items per page (default 20, max 50) |

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Senior Architect",
      "slug": "senior-architect-foster-partners-london",
      "company_name": "Foster + Partners",
      "company_logo_url": null,
      "location_text": "London, UK",
      "country": "GB",
      "city": "London",
      "category": {
        "id": 1,
        "name": "Architect",
        "slug": "architect"
      },
      "seniority_level": "senior",
      "remote_type": "hybrid",
      "salary_min": 60000,
      "salary_max": 80000,
      "salary_currency": "GBP",
      "salary_period": "year",
      "employment_type": "full_time",
      "is_featured": false,
      "posted_at": "2026-01-15T00:00:00Z",
      "is_saved": false
    }
  ],
  "meta": {
    "current_page": 1,
    "last_page": 5,
    "per_page": 20,
    "total": 98
  }
}
```

---

#### `GET /api/v1/jobs/{slug}`
Single job detail.

**Response** `200 OK`:
```json
{
  "data": {
    "id": "uuid",
    "title": "Senior Architect",
    "slug": "senior-architect-foster-partners-london",
    "description_html": "<p>Full HTML description...</p>",
    "company_name": "Foster + Partners",
    "company_website": "https://fosterandpartners.com",
    "company_logo_url": null,
    "location_text": "London, UK",
    "country": "GB",
    "state": null,
    "city": "London",
    "category": { "id": 1, "name": "Architect", "slug": "architect" },
    "tags": [
      { "id": 1, "name": "Revit", "slug": "revit" }
    ],
    "seniority_level": "senior",
    "remote_type": "hybrid",
    "salary_min": 60000,
    "salary_max": 80000,
    "salary_currency": "GBP",
    "salary_period": "year",
    "employment_type": "full_time",
    "apply_url": "https://apply.here.com/123",
    "source": { "name": "Adzuna" },
    "is_featured": false,
    "is_saved": false,
    "posted_at": "2026-01-15T00:00:00Z",
    "expires_at": "2026-02-15T00:00:00Z"
  }
}
```

---

### Categories

#### `GET /api/v1/categories`
List all active job categories.

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": 1,
      "name": "Architect",
      "slug": "architect",
      "icon": "building",
      "jobs_count": 45
    }
  ]
}
```

---

### Saved Jobs

#### `POST /api/v1/saved-jobs`
Save a job.

**Auth**: Required (Sanctum)

**Request Body**:
```json
{ "job_id": "uuid" }
```

**Response** `201 Created`

---

#### `DELETE /api/v1/saved-jobs/{job_id}`
Remove a saved job.

**Auth**: Required (Sanctum)

**Response** `204 No Content`

---

#### `GET /api/v1/saved-jobs`
List user's saved jobs.

**Auth**: Required (Sanctum)

**Response**: Same format as `GET /api/v1/jobs`

---

### Job Alerts (Phase 2)

#### `GET /api/v1/alerts`
List user's job alerts.

#### `POST /api/v1/alerts`
Create a job alert.

#### `PUT /api/v1/alerts/{id}`
Update a job alert.

#### `DELETE /api/v1/alerts/{id}`
Delete a job alert.

---

## 3. Public Job Submission

### `POST /api/v1/jobs/submit`
Public form submission (no auth required, reCAPTCHA protected).

**Request Body**:
```json
{
  "title": "Architect - Residential Projects",
  "description": "We are looking for...",
  "company_name": "Studio XYZ",
  "company_website": "https://studiox.com",
  "location_text": "New York, USA",
  "remote_type": "hybrid",
  "employment_type": "full_time",
  "apply_url": "https://studiox.com/careers",
  "apply_email": "jobs@studiox.com",
  "submitter_email": "poster@email.com",
  "recaptcha_token": "..."
}
```

**Response** `201 Created`:
```json
{
  "message": "Job submitted successfully. It will be reviewed by our team.",
  "id": "uuid"
}
```

---

## Error Responses

All errors follow:
```json
{
  "message": "Human-readable error",
  "errors": {
    "field": ["Validation error"]
  }
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Unprocessable Entity |
| 429 | Rate Limited |
| 500 | Server Error |
