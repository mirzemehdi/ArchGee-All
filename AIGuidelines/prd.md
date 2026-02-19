# PRODUCT REQUIREMENTS DOCUMENT (PRD)
Project Name: ArchGee
Version: 1.1.0 (Revised)

==================================================
## 1. PRODUCT OVERVIEW
==================================================

ArchGee is a niche AI-powered job aggregation platform focused exclusively on:

- Architects
- Interior Designers
- Landscape Architects
- Urban Designers / Urban Planners
- BIM Specialists
- Project Managers (built-environment)
- Sustainability Consultants
- Heritage / Conservation Consultants
- Other built-environment professionals

The platform aggregates jobs from APIs, permitted scraping sources, and manual job submissions.

**There are NO employer accounts.**
Anyone can submit a job using a public "Post Job" form.
All submissions go through admin moderation before publishing.

The system exposes REST APIs for:
- Web frontend (Laravel TALL stack)
- Future mobile apps (Flutter/React Native)

Primary differentiation:
- AI-powered relevance filtering (auto-rejects non-architecture jobs)
- Clean niche focus on built-environment professions
- Google Jobs indexing via schema.org structured data
- Modular multi-source ingestion pipeline
- Smart salary extraction and normalization

==================================================
## 2. TECH STACK
==================================================

**Foundation**: SaaSykit boilerplate (Laravel 12, TALL stack)

**Backend**:
- Laravel 12 (PHP 8.2+)
- MySQL (via Docker/Sail — production may use PostgreSQL)
- Redis (queues via Horizon, cache, rate limiting)
- Laravel Sanctum (API authentication)

**Frontend**:
- Blade + Livewire 4 + Alpine.js + Tailwind CSS 4 + DaisyUI 5
- Vite 7 for asset compilation

**Admin Panel**:
- Filament 5 (existing admin at /admin, user dashboard at /dashboard)

**Search**:
- Meilisearch via Laravel Scout (primary)
- MySQL full-text as fallback

**Scraping Microservice** (Phase 2):
- Python 3.12+
- Pydantic for data validation
- Adapter pattern per source
- Inspired by: https://github.com/speedyapply/JobSpy

**External Job Source Integrations**:
- Adzuna API (MVP — first integration)
- CareerJet API
- Jooble API
- LinkedIn Jobs (if API access available)

**AI Providers**:
- Primary: OpenAI (gpt-4o-mini for classification)
- Fallback: Anthropic Claude / Mistral

**Inspiration / Feature Reference**:
- Job board features: https://www.jobboardly.com/
- Post job UI: https://androidjobs.io/jobs/new

==================================================
## 3. HIGH-LEVEL ARCHITECTURE
==================================================

```
[Manual Submission]  [Adzuna API]  [Python Scrapers]  [Other APIs]
        |                 |               |                |
        v                 v               v                v
   POST /api/v1/jobs/submit    POST /api/ingest/jobs
                    |                      |
                    v                      v
              Normalization Layer (Laravel Service)
                         |
                         v
              AI Enrichment Queue (Redis/Horizon)
              ├── Stage 1: Relevance Classification
              ├── Stage 2: Salary Extraction
              ├── Stage 3: Work Type Detection
              └── Stage 4: Seniority Detection
                         |
                         v
              Moderation Queue (Filament Admin)
                         |
                         v
              Published Jobs (Meilisearch Index)
                         |
                         v
              Public REST API + Web Frontend
                         |
                         v
              Web App + Future Mobile App
```

==================================================
## 4. CORE FEATURES
==================================================

### 4.1 Job Aggregation
- Import from external APIs (Adzuna first)
- Import from Python scrapers (Phase 2)
- Public job submission form (reCAPTCHA protected)
- Duplicate detection via `source_job_id` + title/company hash
- Automatic expiry of old jobs (30 days default)

### 4.2 AI Processing Pipeline
- **Relevance classification**: Is this a built-environment job? (auto-reject if not)
- **Category detection**: Assign to architect/interior designer/etc.
- **Salary extraction**: Parse salary from description text
- **Remote/Hybrid/Onsite detection**: Classify work arrangement
- **Seniority detection**: Intern → Junior → Mid → Senior → Lead → Principal → Director
- All stages run as chained queue jobs via Horizon
- See: `AIGuidelines/ai_prompts.md` for detailed prompts

### 4.3 Moderation (Filament Admin)
- Status workflow: Pending → Approved / Rejected / Expired
- Admin can edit all job fields before publishing
- Bulk actions: approve, reject, delete
- Filter by status, source, category, date
- AI-rejected jobs visible in a separate tab for review

### 4.4 Job Search & Discovery
- Full-text keyword search (Meilisearch)
- Category filter
- Location filter (country, city, text search)
- Remote type filter (remote/hybrid/onsite)
- Salary range filter
- Seniority level filter
- Employment type filter
- Sort: latest, salary high/low, relevance

### 4.5 Public "Post Job" Form
Fields:
- Job title (required)
- Company name (required)
- Company website (optional)
- Job description (required, rich text editor)
- Location (required)
- Remote type: Remote / Hybrid / Onsite (required)
- Employment type: Full-time / Part-time / Contract / Freelance / Internship (required)
- Apply URL or Apply Email (at least one required)
- Submitter email (optional, for status notifications)
- reCAPTCHA verification
- Submit → status set to `pending`

### 4.6 User Features (Optional Accounts)
Leverages existing SaaSykit user system:
- Save/bookmark jobs
- Job alerts — email notifications for new matching jobs (Phase 2)
- View saved jobs list

### 4.7 SEO / Google Jobs
- schema.org JobPosting structured data on every job detail page
- Canonical URLs with descriptive slugs
- Dynamic sitemap via spatie/laravel-sitemap
- Open Graph meta tags for social sharing
- See: `AIGuidelines/seo_guidelines.md` for full spec

### 4.8 Job Detail Page
- Full job description (sanitized HTML)
- Company info and logo
- Location with map placeholder
- Salary range (if available)
- Category, seniority, remote type badges
- "Apply Now" button (external link)
- "Save Job" button (logged-in users)
- "Similar Jobs" section
- Breadcrumbs
- Social share buttons
- Google Jobs JSON-LD

### 4.9 Analytics (Admin)
- Job views count
- Apply clicks count
- Jobs by source breakdown
- Jobs by category/status breakdown

==================================================
## 5. USER ROLES
==================================================

| Role | Access | Auth |
|------|--------|------|
| Admin | Filament admin panel, all CRUD | Email/password + 2FA |
| Candidate | Save jobs, alerts, profile | Email/password or social login (existing SaaSykit auth) |
| Scraper Service | Ingest API only | Sanctum API token with `ingest:jobs` ability |
| Anonymous | Browse jobs, post job form, search | None |

==================================================
## 6. DATA MODEL
==================================================

See `AIGuidelines/db_schema.md` for the complete normalized database schema.

**Core Tables** (new):
- `jobs` — main job listings (UUID PKs)
- `job_categories` — architect, interior designer, etc.
- `job_sources` — Adzuna, manual, scrapers
- `job_tags` — skills/tools tags (Revit, AutoCAD, etc.)
- `job_tag` — pivot table
- `saved_jobs` — user bookmarks
- `job_alerts` — saved search alerts (Phase 2)
- `job_applications_clicks` — analytics

**Existing Tables** (from SaaSykit, reused):
- `users` — extended with job board features
- `personal_access_tokens` — Sanctum tokens for scraper auth

==================================================
## 7. API SPECIFICATION
==================================================

See `AIGuidelines/api_endpoints.md` for the complete API specification.

**Summary**:
- `POST /api/ingest/jobs` — bulk job ingestion (scraper auth)
- `POST /api/ingest/job` — single job ingestion (scraper auth)
- `GET /api/v1/jobs` — list jobs with filters
- `GET /api/v1/jobs/{slug}` — job detail
- `GET /api/v1/categories` — list categories
- `POST /api/v1/jobs/submit` — public job submission
- `POST /api/v1/saved-jobs` — save a job (auth required)
- `DELETE /api/v1/saved-jobs/{job_id}` — unsave (auth required)
- `GET /api/v1/saved-jobs` — list saved jobs (auth required)

==================================================
## 8. AI ENRICHMENT
==================================================

See `AIGuidelines/ai_prompts.md` for detailed prompt templates and pipeline.

**Summary**:
- 4-stage pipeline: Relevance → Salary → Work Type → Seniority
- Chained queue jobs with retry and fallback
- Cost-efficient: gpt-4o-mini, truncated descriptions
- Results stored on job model + optional AI log table

==================================================
## 9. PYTHON SCRAPER
==================================================

See `AIGuidelines/scraper_guidelines.md` for the full scraper contract.

**Summary**:
- Adapter pattern per source
- Pydantic data validation
- Pre-filtering by architecture keywords
- Deduplication before sending to Laravel
- POST results to `/api/ingest/jobs`

==================================================
## 10. NON-FUNCTIONAL REQUIREMENTS
==================================================

- **Rate Limiting**: API endpoints rate-limited (100/min for ingest, 60/min for public)
- **Authentication**: Sanctum tokens for scrapers, optional for users
- **Queue Processing**: All AI enrichment and notifications via Horizon
- **Performance**: Job listing page < 500ms, search < 300ms
- **Caching**: Redis cache for category counts, popular searches
- **Security**: XSS protection via HTML sanitization, CSRF on forms, reCAPTCHA
- **Mobile-friendly**: Responsive Tailwind + DaisyUI design
- **SEO**: Google Jobs schema, sitemap, canonical URLs
- **Monitoring**: Horizon dashboard, Telescope (dev), error logging

==================================================
## 11. PHASED ROADMAP
==================================================

### MVP (Phase 1)
- [x] Database schema (jobs, categories, sources, tags)
- [x] Job model with UUID, slug generation, scopes
- [x] Filament admin resource for job moderation
- [x] Public "Post Job" form (Livewire)
- [x] Job listing page with search and filters
- [x] Job detail page with Google Jobs schema
- [x] Ingest API endpoint (single + bulk)
- [x] AI relevance classification
- [x] AI category/salary/remote/seniority detection
- [x] Public REST API (jobs, categories)
- [x] Meilisearch integration via Scout
- [x] First external source integration (Adzuna)
- [x] Basic analytics (views, clicks)

### Phase 2
- [ ] Python scraper microservice
- [x] Additional API sources (CareerJet, Jooble, Reed)
- [x] Job alerts (email notifications)
- [ ] Salary extraction improvements
- [ ] Company profiles (auto-generated from job data)
- [x] Advanced analytics dashboard

### Phase 3
- [ ] Mobile app (Kotlin Multiplatform)
- [ ] AI-powered job recommendations
- [ ] Resume parsing and matching
- [ ] Premium job listings (paid)
- [ ] Employer self-service portal

==================================================
END OF DOCUMENT
