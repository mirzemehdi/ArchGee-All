# ArchGee Database Schema

## Overview
Normalized database structure for the ArchGee job board. Built on top of the existing SaaSykit schema (users, subscriptions, etc.).

---

## New Tables

### `job_categories`
Lookup table for job categories/disciplines.

| Column | Type | Constraints |
|--------|------|-------------|
| id | bigint (auto) | PK |
| name | varchar(100) | unique, not null |
| slug | varchar(100) | unique, not null |
| description | text | nullable |
| icon | varchar(50) | nullable |
| is_active | boolean | default true |
| sort_order | int | default 0 |
| created_at | timestamp | |
| updated_at | timestamp | |

**Seed values**: Architect, Interior Designer, Landscape Architect, Urban Designer, Urban Planner, BIM Specialist, Project Manager, Sustainability Consultant, Heritage Consultant, Other

---

### `job_sources`
Tracks where jobs originate from.

| Column | Type | Constraints |
|--------|------|-------------|
| id | bigint (auto) | PK |
| name | varchar(100) | unique, not null |
| slug | varchar(100) | unique, not null |
| type | enum | api, scraper, rss, manual |
| base_url | varchar(255) | nullable |
| api_token | varchar(255) | nullable, encrypted |
| is_enabled | boolean | default true |
| last_fetched_at | timestamp | nullable |
| config | json | nullable (adapter-specific config) |
| created_at | timestamp | |
| updated_at | timestamp | |

---

### `jobs`
Core job listings table.

| Column | Type | Constraints |
|--------|------|-------------|
| id | uuid | PK |
| title | varchar(255) | not null, indexed |
| slug | varchar(300) | unique, not null |
| description | text | not null |
| description_html | text | nullable (sanitized HTML) |
| company_name | varchar(255) | not null, indexed |
| company_website | varchar(255) | nullable |
| company_logo_url | varchar(500) | nullable |
| location_text | varchar(255) | nullable (raw location string) |
| country | varchar(2) | nullable (ISO 3166-1 alpha-2) |
| state | varchar(100) | nullable |
| city | varchar(100) | nullable |
| latitude | decimal(10,7) | nullable |
| longitude | decimal(10,7) | nullable |
| job_category_id | bigint | FK → job_categories.id, nullable |
| seniority_level | enum | nullable: intern, junior, mid, senior, lead, principal, director |
| remote_type | enum | not null, default onsite: remote, hybrid, onsite |
| salary_min | int unsigned | nullable |
| salary_max | int unsigned | nullable |
| salary_currency | varchar(3) | nullable (ISO 4217) |
| salary_period | enum | nullable: hour, month, year |
| employment_type | enum | not null, default full_time: full_time, part_time, contract, freelance, internship |
| apply_url | varchar(500) | nullable |
| apply_email | varchar(255) | nullable |
| job_source_id | bigint | FK → job_sources.id, nullable |
| source_job_id | varchar(255) | nullable (original ID from source) |
| original_url | varchar(500) | nullable |
| status | enum | not null, default pending: pending, approved, rejected, expired |
| is_featured | boolean | default false |
| ai_relevance_score | decimal(3,2) | nullable (0.00-1.00) |
| ai_category_confidence | decimal(3,2) | nullable |
| ai_processed_at | timestamp | nullable |
| submitter_email | varchar(255) | nullable |
| posted_at | timestamp | nullable |
| approved_at | timestamp | nullable |
| expires_at | timestamp | nullable |
| views_count | int unsigned | default 0 |
| clicks_count | int unsigned | default 0 |
| created_at | timestamp | |
| updated_at | timestamp | |
| deleted_at | timestamp | nullable (soft delete) |

**Indexes**:
- `idx_jobs_status_posted` on (status, posted_at DESC)
- `idx_jobs_category` on (job_category_id)
- `idx_jobs_remote_type` on (remote_type)
- `idx_jobs_seniority` on (seniority_level)
- `idx_jobs_country_city` on (country, city)
- `idx_jobs_source_job` on (job_source_id, source_job_id) — for dedup
- `idx_jobs_expires` on (expires_at)
- Full-text index on (title, description) for basic MySQL search fallback

---

### `job_tags`
Tags for additional job metadata.

| Column | Type | Constraints |
|--------|------|-------------|
| id | bigint (auto) | PK |
| name | varchar(50) | unique, not null |
| slug | varchar(50) | unique, not null |
| created_at | timestamp | |
| updated_at | timestamp | |

---

### `job_tag` (pivot)
Many-to-many between jobs and tags.

| Column | Type | Constraints |
|--------|------|-------------|
| job_id | uuid | FK → jobs.id, cascade |
| tag_id | bigint | FK → job_tags.id, cascade |

**Primary key**: (job_id, tag_id)

---

### `saved_jobs`
Users can save/bookmark jobs.

| Column | Type | Constraints |
|--------|------|-------------|
| id | bigint (auto) | PK |
| user_id | bigint | FK → users.id, cascade |
| job_id | uuid | FK → jobs.id, cascade |
| created_at | timestamp | |

**Unique**: (user_id, job_id)

---

### `job_alerts`
Email alerts for saved searches (Phase 2).

| Column | Type | Constraints |
|--------|------|-------------|
| id | bigint (auto) | PK |
| user_id | bigint | FK → users.id, cascade |
| name | varchar(100) | nullable |
| filters | json | not null (keyword, category, location, remote, salary) |
| frequency | enum | not null: daily, weekly |
| is_active | boolean | default true |
| last_sent_at | timestamp | nullable |
| created_at | timestamp | |
| updated_at | timestamp | |

---

### `job_applications_clicks`
Track apply button clicks for analytics.

| Column | Type | Constraints |
|--------|------|-------------|
| id | bigint (auto) | PK |
| job_id | uuid | FK → jobs.id, cascade |
| user_id | bigint | FK → users.id, nullable |
| ip_address | varchar(45) | nullable |
| user_agent | varchar(500) | nullable |
| created_at | timestamp | |

---

## Relationships Summary

```
job_categories  1 ──── N  jobs
job_sources     1 ──── N  jobs
jobs            N ──── M  job_tags (via job_tag pivot)
users           N ──── M  jobs (via saved_jobs)
users           1 ──── N  job_alerts
jobs            1 ──── N  job_applications_clicks
```

## Notes
- Jobs use UUID primary keys for public exposure (no sequential IDs)
- Soft deletes on jobs to preserve analytics data
- The `source_job_id` + `job_source_id` composite is used for deduplication
- `description_html` stores sanitized HTML (via mews/purifier) for rich display
- `salary_min`/`salary_max` stored as integers (annual normalized values for filtering)
- Geographic data (lat/lng) enables future radius search
