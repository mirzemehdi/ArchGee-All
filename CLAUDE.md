# CLAUDE.md — ArchGee Project

## Project Overview

**ArchGee** is an AI-powered niche job aggregation platform exclusively for built-environment professionals (architects, interior designers, landscape architects, urban designers, BIM specialists, sustainability consultants, heritage consultants).

**Key differentiators**: No employer accounts, AI-powered relevance filtering, Google Jobs schema, multi-source ingestion pipeline, clean niche focus.

## Monorepo Structure

```
ArchGee-All/                          # Root (git repo)
├── ArchGee-Website/                  # Laravel 12 app (also its own git repo)
├── python-scraper/                   # Python 3.12+ job scraper
├── AIGuidelines/                     # Product & technical documentation
│   ├── prd.md                        # Product Requirements Document
│   ├── db_schema.md                  # Database schema spec
│   ├── api_endpoints.md              # API contract
│   ├── ai_prompts.md                 # AI enrichment prompts & config
│   ├── scraper_guidelines.md         # Python scraper contract
│   ├── seo_guidelines.md             # SEO & Google Jobs schema
│   ├── job_sources_guideline.md      # Job source APIs & compliance
│   ├── ui_verification.md            # UI design system & components
│   └── SETUP_GUIDE.md               # Developer setup guide
└── Assets/                           # Brand assets (logos, images)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | Laravel 12, PHP 8.2+ |
| **Frontend** | TALL stack — Tailwind CSS 4, Alpine.js, Livewire 4, DaisyUI 5 |
| **Admin** | Filament 5 (two panels: `/admin` + `/dashboard`) |
| **Database** | MySQL 8.0 (via Docker/Sail) |
| **Cache/Queue** | Redis, Laravel Horizon |
| **Search** | Meilisearch via Laravel Scout (optional, falls back to MySQL LIKE) |
| **Auth** | Laravel Sanctum, Socialite, Filament Breezy |
| **AI** | OpenAI (gpt-4o-mini) / Anthropic / Mistral for job enrichment |
| **Assets** | Vite 7 |
| **Scraper** | Python 3.12+, httpx, Pydantic, Click CLI |
| **Boilerplate** | SaaSykit (subscriptions, payments, blog, roadmap) |

## Development Commands

All commands run from `ArchGee-Website/` using Laravel Sail:

```bash
# Start/stop environment
./vendor/bin/sail up -d
./vendor/bin/sail down

# Frontend
./vendor/bin/sail npm run dev        # Vite hot reload
./vendor/bin/sail npm run build      # Production build

# Backend
./vendor/bin/sail artisan migrate:fresh --seed   # Reset DB
./vendor/bin/sail artisan horizon                # Queue worker
./vendor/bin/sail artisan schedule:run           # Run scheduled tasks

# Job source fetching
./vendor/bin/sail artisan jobs:fetch-reed
./vendor/bin/sail artisan jobs:fetch-adzuna
./vendor/bin/sail artisan jobs:fetch-careerjet
./vendor/bin/sail artisan jobs:fetch-jooble

# Testing & quality
./vendor/bin/sail test                           # PHPUnit
./vendor/bin/sail test --filter=JobTest          # Specific test
vendor/bin/phpstan analyse                       # Static analysis (level 3)
vendor/bin/pint                                  # Code formatter (PSR-12)

# Python scraper (from python-scraper/)
python main.py --all                             # Fetch all sources
python main.py --source adzuna --country gb,us   # Specific source/country
```

## Key URLs (Development)

- **App**: http://localhost:8080
- **Admin Panel**: http://localhost:8080/admin
- **User Dashboard**: http://localhost:8080/dashboard
- **Horizon (queues)**: http://localhost:8080/horizon
- **Telescope (debug)**: http://localhost:8080/telescope
- **Mailpit (email)**: http://localhost:8025

## Architecture

### Core Pipeline

```
Sources (APIs, scrapers, manual form)
    → Ingest API (/api/ingest/jobs)
    → Normalization + Dedup (source_job_id + hash)
    → AI Enrichment Queue (4 chained stages)
        1. Relevance Classification (is this an architecture job?)
        2. Salary Extraction (parse salary from description)
        3. Work Type Detection (remote/hybrid/onsite)
        4. Seniority Detection (junior/mid/senior/etc.)
    → Moderation (Filament admin: pending → approved/rejected)
    → Published (Meilisearch index, public API, web)
```

### User Roles

- **Admin**: Filament panel, moderate jobs, manage sources/categories
- **Candidate**: Save jobs, create alerts, browse (authenticated)
- **Scraper Service**: Ingest API with Sanctum token (`ingest:jobs` ability)
- **Anonymous**: Browse jobs, submit via public form

### ArchGee-Specific Models (app/Models/)

| Model | Purpose |
|-------|---------|
| `Job` | Core job posting (UUID PK, soft deletes, Scout searchable) |
| `JobCategory` | Category taxonomy (slug, icon, sort_order) |
| `JobSource` | External sources (api_token encrypted, config JSON) |
| `JobTag` | Tags (M2M via `job_tag` pivot) |
| `JobAlert` | User alert subscriptions (filters JSON, frequency) |
| `SavedJob` | User bookmarks (pivot: user_id + job_id) |
| `JobApplicationClick` | Apply button click tracking |

### ArchGee-Specific Services (app/Services/)

| Service | Purpose |
|---------|---------|
| `JobService` | Core job CRUD, filtering, duplicate detection, view tracking |
| `JobAlertService` | Alert CRUD, matching jobs to alert filters |
| `AiEnrichmentService` | AI pipeline (OpenAI/Anthropic/Mistral), 4 classification stages |
| `ReedFetchService` | Reed.co.uk API integration (UK only) |
| `AdzunaFetchService` | Adzuna API (16 countries) |
| `CareerjetFetchService` | Careerjet API (16 locales, Basic auth) |
| `JoobleFetchService` | Jooble API (13 countries) |
| `PostHogAnalyticsService` | Event analytics tracking |

### Enums (app/Constants/)

| Enum | Values |
|------|--------|
| `JobStatus` | PENDING, APPROVED, REJECTED, EXPIRED |
| `RemoteType` | REMOTE, HYBRID, ONSITE |
| `SeniorityLevel` | INTERN, JUNIOR, MID, SENIOR, LEAD, PRINCIPAL, DIRECTOR |
| `EmploymentType` | FULL_TIME, PART_TIME, CONTRACT, FREELANCE, INTERNSHIP |
| `SalaryPeriod` | HOUR, DAY, MONTH, YEAR |
| `JobSourceType` | API, MANUAL |
| `AlertFrequency` | DAILY, WEEKLY |

### Queue Jobs (app/Jobs/)

- `EnrichJobWithAi` — Async AI enrichment (queue: `ai-enrichment`, 3 retries, 30s backoff). Auto-approves API-imported jobs passing relevance check.
- `SendJobAlerts` — Match jobs to alert filters and send emails.

### Console Commands (app/Console/Commands/)

- `FetchReedJobsCommand`, `FetchAdzunaJobsCommand`, `FetchCareerjetJobsCommand`, `FetchJoobleJobsCommand` — Source fetchers (scheduled every 6hrs)
- `ExpireOldJobsCommand` — Mark jobs expired after 30 days
- `SendJobAlertsCommand` — Send matching job alerts
- `GenerateSitemap` — XML sitemap with job/category/location pages

## API Endpoints

### Ingest API (Sanctum token auth, 100 req/min)

```
POST /api/ingest/job       # Single job ingest
POST /api/ingest/jobs      # Bulk ingest (max 100)
GET  /api/ingest/sources   # List available sources
```

### Public REST API v1 (60 req/min)

```
GET  /api/v1/jobs              # List published jobs (filters: q, category, location, country, remote, seniority, employment_type, salary_min/max, sort)
GET  /api/v1/jobs/{slug}       # Job detail (increments view count)
POST /api/v1/jobs/submit       # Public submission (reCAPTCHA)
GET  /api/v1/categories        # Categories with job counts
```

### Authenticated Endpoints (Sanctum)

```
GET    /api/v1/saved-jobs          # User's saved jobs
POST   /api/v1/saved-jobs          # Save a job
DELETE /api/v1/saved-jobs/{jobId}  # Unsave
GET    /api/v1/alerts              # User's alerts
POST   /api/v1/alerts              # Create alert
PUT    /api/v1/alerts/{id}         # Update alert
DELETE /api/v1/alerts/{id}         # Delete alert
```

### Web Routes

```
GET  /jobs                           # Job listing with filters
GET  /jobs/post                      # Public submission form
GET  /jobs/category/{slug}           # Category landing (pSEO)
GET  /jobs/location/{country}        # Country landing (pSEO)
GET  /jobs/location/{country}/{city} # City landing (pSEO)
GET  /jobs/{slug}                    # Job detail page
POST /jobs/{slug}/apply              # Track application click
```

## Job Sources

### Active Sources (Tier 1 — Safe, free, official APIs)

| Source | Coverage | Rate Limit | Notes |
|--------|----------|-----------|-------|
| **Adzuna** | 16 countries | 250 req/day (free) | Best multi-country coverage |
| **Reed.co.uk** | UK only | 1,000 req/day | Strong architecture coverage |
| **Careerjet** | 16 locales | Max page 10, page_size 1-100 | API key (Basic auth), must use tracking URLs, 500ms throttle between requests |
| **Jooble** | 13 countries | Generous (undocumented) | Aggregates 140K+ sources |

### Do NOT Use (ToS violations)

Indeed, LinkedIn, Glassdoor, Google Jobs, JobSpy library — all prohibited.

## Python Scraper (python-scraper/)

- **Architecture**: Adapter pattern per source, Pydantic validation, httpx client
- **Adapters**: `adzuna.py`, `careerjet.py`, `jooble.py` (in `adapters/`)
- **Dedup**: Local SQLite cache (title+company+location hash, 30-day expiry) + server-side dedup
- **Keyword filters**: 56 include keywords (architect, BIM, CAD...), 35 exclude keywords (software architect, DevOps...)
- **Batch size**: 50 jobs per API call to Laravel
- **Schedule**: Every 6 hours (`python main.py --all`)
- **Config**: `.env` with `ARCHGEE_API_URL`, `ARCHGEE_API_TOKEN`, source API keys

## Coding Standards

### PHP / Laravel

Follow `ai/laravel-php-ai-guidelines.md`. Key rules:

- **PSR-12** formatting (enforced by Laravel Pint)
- **camelCase** for methods/variables, **PascalCase** for classes
- **kebab-case** for routes, **snake_case** for config keys
- Use **typed properties** over docblocks
- **Early returns** (happy path last), avoid `else`
- **Constructor property promotion** when all properties can be promoted
- **String interpolation** over concatenation
- Always use **curly braces** for control structures
- **Service layer** for business logic (stateless, injected via DI)
- **DTOs** for complex data between layers
- **Event/Listener** pattern for side effects
- **Queue** long-running tasks (AI, email, webhooks)
- All monetary amounts use the `Money` package
- Translations via `__()` function

### Filament 5 Gotchas

These are critical — Filament 5 changed several property declarations from static to non-static:

- `Page::$view` → `protected string $view` (NOT static)
- `ChartWidget::$maxHeight` → `protected ?string $maxHeight` (NOT static)
- `Widget::$sort` → IS static: `protected static ?int $sort`
- `InteractsWithForms` passes `Schema` objects, NOT `Form` objects — method signatures must use `Schema $schema`

### File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Controllers | Plural + `Controller` | `JobsController` |
| Jobs | Action-based | `EnrichJobWithAi` |
| Events | Tense-based | `JobApproved` |
| Listeners | Action + `Listener` | `SendApprovalNotificationListener` |
| Commands | Action + `Command` | `FetchReedJobsCommand` |
| Mailables | Purpose + `Mail` | `JobAlertMail` |
| Resources | Singular + `Resource` | `JobResource` |
| Enums | Descriptive, no prefix | `JobStatus`, `RemoteType` |

## SEO & Google Jobs

- **Google Jobs JSON-LD** (`JobPosting` schema) on every job detail page
- Required: title, description (HTML), datePosted, validThrough (+30 days), hiringOrganization, jobLocation
- `employmentType` mapping: full_time→FULL_TIME, contract→CONTRACTOR, internship→INTERN
- `jobLocationType`: "TELECOMMUTE" for remote jobs only
- `directApply`: always `false` (external links)
- **URL structure**: `/jobs/{slug}` (format: `{title}-{company}-{city}-{short-id}`)
- **Sitemap**: `spatie/laravel-sitemap`, split if >1000 jobs
- **robots.txt**: Disallow /admin, /dashboard, /api, /checkout, /horizon, /telescope

## UI Design System

### Colors

- **Primary**: `#FF9228` (orange) — CTAs, links, accents
- **Secondary**: `#1E222B` (dark) — backgrounds, text
- **Work type badges**: emerald (remote), blue (hybrid), amber (onsite)
- **No SaaSykit purple/violet** — all purples must be replaced with the orange palette

### Typography & Layout

- **Font**: Poppins (weights 400-700)
- **Radius**: `rounded-xl` or `rounded-full`
- **Buttons**: Primary `bg-primary-500`, Secondary `bg-secondary-950`, Ghost `bg-white/10`
- **Animations**: `fade-in-up`, `pulse-gentle` (CTA), `hover-lift` (cards)

### Responsive Breakpoints

- Mobile: 375px (single column, burger menu)
- Tablet: 768px (2-col grids, inline search)
- Desktop: 1024px+ (full layout, sidebar)

### Accessibility (WCAG AA)

- Color contrast ≥ 4.5:1
- All form labels linked via `for`/`id`
- Focus visible (ring), keyboard navigable
- Semantic HTML (`nav`, `main`, `section`, `footer`)
- `aria-describedby` for error messages

## Database Notes

- Jobs use **UUID** primary keys (not auto-increment)
- **Soft deletes** on jobs (preserves analytics)
- **Deduplication**: `source_job_id` + `job_source_id` composite uniqueness
- `description_html` sanitized via `mews/purifier`
- Salary normalized to annual integers (`salary_min`/`salary_max`)
- Key indexes: `status+posted_at`, `job_category_id`, `remote_type`, `seniority_level`, `country+city`, `source_job_id`, full-text on `title+description`

## AI Enrichment Config

```env
AI_PROVIDER=openai          # openai | anthropic | mistral
AI_MODEL=gpt-4o-mini        # Cost-efficient model
AI_TEMPERATURE=0.1          # Low for deterministic classification
AI_RELEVANCE_THRESHOLD=0.6  # Below = flag for review
```

- Descriptions truncated to 2000 chars for cost efficiency
- Failed enrichment → auto-approve API jobs with "Other" category
- Queue: `ai-enrichment`, 3 retries with 30s exponential backoff

## PostHog Analytics

PostHog requires **two different API keys** for full functionality:

```env
POSTHOG_API_KEY=phc_...               # Project API key — JS SDK (frontend event capture)
POSTHOG_PERSONAL_API_KEY=phx_...      # Personal API key — server-side HogQL queries (admin dashboard)
POSTHOG_HOST=https://us.i.posthog.com # Ingest host (us.i. for US, eu.i. for EU)
```

- **Project API key** (`phc_...`): Used by the JS SDK on the frontend to send events. Get from PostHog Project Settings.
- **Personal API key** (`phx_...`): Used by `PostHogAnalyticsService` for server-side HogQL queries. Get from PostHog User Settings > Personal API Keys.
- The service auto-derives the API host (`us.posthog.com`) from the ingest host (`us.i.posthog.com`).
- Admin dashboard: `/admin/product-analytics` — shows KPIs, unique visitors, funnels, trends.

## Testing

```bash
# Laravel tests
./vendor/bin/sail test
./vendor/bin/sail test --filter=JobTest
./vendor/bin/sail test --coverage

# Static analysis
vendor/bin/phpstan analyse    # Level 3

# Code formatting
vendor/bin/pint

# Python scraper tests
cd python-scraper && python -m pytest
```

## Common Gotchas — Alpine.js + Livewire

### NEVER use `<template x-if>` inside SVG elements
SVG elements parse `<template>` as an SVG element (not HTMLTemplateElement), so `.content` is undefined. This causes: `"can't access property 'cloneNode', e.content is undefined"`. **Fix**: Use `x-show` on separate SVG elements instead:
```blade
{{-- BAD: causes cloneNode error --}}
<svg>
    <template x-if="condition"><path d="..."/></template>
</svg>

{{-- GOOD: use x-show on separate SVGs --}}
<svg x-show="condition"><path d="..."/></svg>
<svg x-show="!condition"><path d="..."/></svg>
```

### Multi-step forms with `x-show`: add `novalidate` to `<form>`
When using `x-show` to hide/show form steps, hidden inputs with `required` attributes trigger browser error "An invalid form control is not focusable". **Fix**: Add `novalidate` to the `<form>` tag and rely on server-side (Livewire) validation.

### Don't mix `wire:model` and `x-model` on the same input
When using `@entangle` for Alpine ↔ Livewire sync, use only `x-model` on the input. Adding both `wire:model` and `x-model` creates conflicting bindings. **Fix**: Use `@entangle('property')` in x-data and `x-model="property"` on the input (no `wire:model`).

### reCAPTCHA in Livewire forms
Don't use `recaptchaApiJsScriptTag()` / `recaptchaApiChallengeTag()` in Livewire components — they're for traditional form POST. **Fix**: Follow the existing pattern in `resources/views/livewire/auth/partials/recaptcha.blade.php`:
- Add `public $recaptcha` property to Livewire component
- Use `htmlFormSnippet(["callback" => "onRecaptchaSuccess"])` inside `wire:ignore`
- Add hidden input with `x-on:captcha-success.window="$wire.recaptcha = $event.detail.token"`
- Load JS API via `@push('tail') {!! htmlScriptTagJsApi() !!} @endpush`

## Important References

- **Coding guidelines**: `ArchGee-Website/ai/laravel-php-ai-guidelines.md`
- **Boilerplate docs**: `ArchGee-Website/AGENTS.md` (SaaSykit original)
- **All guideline docs**: `AIGuidelines/` directory (PRD, schema, API, AI prompts, SEO, UI, sources)
