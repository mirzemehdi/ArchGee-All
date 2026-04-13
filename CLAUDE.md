# CLAUDE.md — ArchGee Project

## Project Overview

**ArchGee** is an AI-powered niche job aggregation platform exclusively for built-environment professionals (architects, interior designers, landscape architects, urban designers, BIM specialists, sustainability consultants, heritage consultants).

**Key differentiators**: No employer accounts, AI-powered relevance filtering, Google Jobs schema, multi-source ingestion pipeline, clean niche focus.

## Monorepo Structure

```
ArchGee-All/                          # Root (git repo)
├── ArchGee-Website/                  # Laravel 12 app (also its own git repo)
│   ├── blog-content/                 # Blog content system
│   │   ├── blog-guidelines.md        # Writing rules, tone, SEO, structure
│   │   ├── blog-topics.json          # 100 SEO topics with status tracking
│   │   └── posts/{slug}.mdx          # Blog posts (MDX with YAML frontmatter)
├── ArchGee-MobileApp/                # Kotlin Multiplatform mobile app (Android + iOS)
│   ├── composeApp/                   # Main shared app module (Compose Multiplatform)
│   ├── designsystem/                 # Reusable UI component library (40+ composables)
│   ├── iosApp/                       # Xcode wrapper for iOS
│   └── distribution/                 # Release assets (keystore, release notes)
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
│   ├── mobile_app_guidelines.md      # Mobile app architecture & integration
│   └── SETUP_GUIDE.md               # Developer setup guide
└── Assets/                           # Brand assets (logos, images)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | Laravel 12, PHP 8.2+ |
| **Frontend** | TALL stack — Tailwind CSS 4, Alpine.js, Livewire 4, DaisyUI 5 |
| **Admin** | Filament 5 (two panels: `/admin` + `/dashboard`) |
| **Database** | MySQL 8.4 (prod Docker) / MySQL 8.0 (dev Sail) |
| **Cache/Queue** | Redis, Laravel Horizon |
| **Search** | Meilisearch via Laravel Scout (optional, falls back to MySQL LIKE) |
| **Auth** | Laravel Sanctum, Socialite, Filament Breezy |
| **AI** | OpenAI (gpt-4o-mini) / Anthropic / Mistral for job enrichment |
| **Assets** | Vite 7 |
| **Scraper** | Python 3.12+, httpx, Pydantic, Click CLI |
| **Mobile App** | Kotlin Multiplatform, Compose Multiplatform, Ktor, Koin, Room |
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

## Deployment (Production — Docker + Dokploy)

**No deploy.php / Deployer is used.** Production runs on Docker Compose via Dokploy on VPS.

### Architecture

```
Dokploy (VPS)
  └─ Traefik (TLS termination, routing)
      └─ docker-compose.prod.yml
          ├── app          — FrankenPHP 1.4 (PHP 8.3, Caddy) — web server
          ├── horizon      — Laravel Horizon queue worker
          ├── scheduler    — php artisan schedule:work
          ├── mysql        — MySQL 8.4 (internal only, no host ports)
          ├── redis        — Redis 7 (internal only, password auth)
          └── meilisearch  — Meilisearch v1.12 (internal only)
```

### Key Files

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` | Production orchestration (Dokploy-ready) |
| `Dockerfile` | Multi-stage build: Composer → Node/Vite → FrankenPHP runtime |
| `docker/production/entrypoint.sh` | Startup: permissions, caching, migrations, sitemap |
| `docker/production/Caddyfile` | Caddy config + SEO file rewrites |
| `docker/production/php.ini` | OPcache, memory limits, upload limits |
| `.dockerignore` | Excludes dev files from production image |

### How Deployment Works

1. Dokploy pulls code from git, builds Docker images via `Dockerfile`
2. Multi-stage build: Composer install → npm build → FrankenPHP runtime
3. `entrypoint.sh` runs on each container start (role-based via `CONTAINER_ROLE`):
   - **All roles**: `config:cache`, `route:cache`, `storage:link`, fix permissions
   - **App role only**: `migrate --force`, `db:seed`, create admin user, `app:export-configs`, `blog:import --all`, `app:generate-sitemap --force`
4. CMD hands off to: `frankenphp run` (app), `artisan horizon` (horizon), `artisan schedule:work` (scheduler)

### Shared Storage (Docker Volume)

All three app containers share `app-storage:/app/storage/app/public` volume. This is critical for:
- **Sitemap/robots.txt**: Generated files are written to `storage/app/public/` (shared volume), then served via Caddy rewrites (`/sitemap.xml` → `/storage/sitemap.xml`)
- **User uploads**: Accessible via `storage:link` symlink (`public/storage/` → `storage/app/public/`)

### Permissions (Docker)

- Entrypoint runs `chown -R www-data:www-data storage/ bootstrap/cache/` + `chmod 775`
- FrankenPHP handles privilege management internally
- `storage/` and `bootstrap/cache/` must be writable by `www-data`
- The shared Docker volume preserves ownership across container restarts

### Security Notes

- MySQL/Redis/Meilisearch have **no host port bindings** — only reachable within Docker network
- Redis supports password auth via `REDIS_PASSWORD` env var (recommended for production)
- `DB_ROOT_PASSWORD` can be set separately from `DB_PASSWORD`
- `SERVER_NAME=:80` for Dokploy (TLS handled by Traefik upstream)
- `.env` file is never baked into the Docker image (listed in `.dockerignore`)

### Production Deploy Checklist

```bash
# On VPS (one-time setup)
# 1. Set up Dokploy, point it to git repo
# 2. Configure .env with production values in Dokploy
# 3. Ensure ADMIN_EMAIL, ADMIN_PASSWORD are set for first deploy
# 4. Set REDIS_PASSWORD to a strong value
# 5. Set DB_ROOT_PASSWORD separately from DB_PASSWORD
# 6. Set MOBILE_API_KEY to a strong random value (used by mobile app X-Api-Key header)
# 7. Set FIREBASE_PROJECT_ID to your Firebase project ID (for mobile auth token verification)
# 8. Set REVENUECAT_API_KEY (secret sk_...) + REVENUECAT_PROJECT_ID (for mobile credit purchases)
# 9. Set CLOUDFLARE_R2_* env vars (access key, secret, bucket, endpoint, public URL)
# 10. Set TELESCOPE_ENABLED=true to enable Telescope in production
# 11. Set MEILISEARCH_KEY to a strong random string (min 16 bytes)

# Manual commands (if needed)
docker compose -f docker-compose.prod.yml exec app php artisan app:generate-sitemap --force
docker compose -f docker-compose.prod.yml exec app php artisan migrate:status
docker compose -f docker-compose.prod.yml logs -f horizon
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

### Geo-Based Job Prioritization

Jobs are sorted with the user's detected country first, then remote jobs, then everything else — on both web (`/jobs`) and API (`/api/v1/jobs`). No filtering — all jobs still shown.

- **Detection**: `GeoLocationService` checks Cloudflare `CF-IPCountry` header first, falls back to `ip-api.com` free API. Cached per IP for 24h.
- **Scope**: `Job::scopeCountryFirst(?string $countryCode)` adds `ORDER BY CASE WHEN country = ? THEN 0 WHEN remote_type = 'remote' THEN 1 ELSE 2 END` before featured/posted_at ordering.
- **Applied in**: `JobService::getPublishedJobs()` (via `$countryPriority` param), `JobsController::index()`, `Api\V1\JobController::index()`, homepage route.
- **Fallback**: localhost/unknown IP → `null` → no prioritization, normal order.
- **Privacy**: Disclosed in privacy policy under "IP-Based Location Detection" section.

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
| `AIGeneration` | AI tool generation tracking (UUID PK, Replicate prediction ID, status, input/output images) |

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
| `GeoLocationService` | IP → country detection (CF-IPCountry header + ip-api.com fallback, cached 24h) |
| `PostHogAnalyticsService` | Event analytics tracking |
| `ToolRegistry` | Singleton — auto-discovers `BaseTool` subclasses in `app/AI/Tools/` |
| `ReplicateService` | Replicate API client (start prediction, poll, download output) |
| `GenerationService` | Orchestrates AI tool generations (create, rate limit, history) |
| `BlogCoverImageService` | Generates 1200x630 PNG cover images for blog posts (Intervention Image v3) |

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
| `GenerationStatus` | QUEUED, RUNNING, COMPLETED, FAILED |

### Queue Jobs (app/Jobs/)

- `EnrichJobWithAi` — Async AI enrichment (queue: `ai-enrichment`, 3 retries, 30s backoff). Auto-approves API-imported jobs passing relevance check.
- `SendJobAlerts` — Match jobs to alert filters and send emails.
- `RunAIToolJob` — Execute AI tool generation via Replicate API (queue: `ai-tools`, 2 retries, 360s timeout).

### Console Commands (app/Console/Commands/)

- `FetchReedJobsCommand`, `FetchAdzunaJobsCommand`, `FetchCareerjetJobsCommand`, `FetchJoobleJobsCommand` — Source fetchers (scheduled every 6hrs)
- `ExpireOldJobsCommand` — Mark jobs expired after 30 days
- `SendJobAlertsCommand` — Send matching job alerts
- `ImportBlogPostCommand` — Import MDX blog posts into DB (`blog:import {slug?} --all --force`)
- `GenerateSitemap` — XML sitemap with job/category/location pages

## API Endpoints

### Ingest API (Sanctum token auth, 100 req/min)

```
POST /api/ingest/job       # Single job ingest
POST /api/ingest/jobs      # Bulk ingest (max 100)
GET  /api/ingest/sources   # List available sources
```

### Public REST API v1 (60 req/min, API key required)

Protected by `VerifyApiKey` middleware — requires `X-Api-Key` header matching `MOBILE_API_KEY` env var. Returns 401 JSON if missing/invalid.

```
GET  /api/v1/jobs              # List published jobs (filters: q, category, location, country, remote, seniority, employment_type, salary_min/max, sort)
GET  /api/v1/jobs/{slug}       # Job detail (increments view count)
POST /api/v1/jobs/submit       # Public submission (reCAPTCHA)
GET  /api/v1/categories        # Categories with job counts
```

### Auth API (API key required, no Sanctum)

```
POST /api/v1/auth/firebase     # Exchange Firebase ID token for Sanctum token (creates/finds user)
```

**Identity resolution** in `AuthController::firebaseExchange`:

1. Look up existing user by `firebase_uid` (stable across anonymous → Google/Apple linking).
2. Fall back to email lookup — handles users who signed up on web with the same Google account.
3. If both lookups return different records (anonymous mobile user just linked a Google email that already owns a separate web account), `UserMergeService` merges them in a transaction: credit balances are summed, owned rows across 13 tables (credit_transactions, ai_generations, saved_jobs, etc.) are reassigned, tokens are revoked, and the source user is deleted. Same email = same account, always.
4. Otherwise create a new user.

Key files:
- `app/Services/UserMergeService.php` — merge logic, table reassignment, pivot conflict handling
- `users.firebase_uid` — nullable unique indexed column (migration: `2026_04_10_120000_add_firebase_uid_to_users_table.php`)
- `ToolController::verifyPurchaseWithRevenueCat()` reads `$user->firebase_uid` directly (RevenueCat customer ID is always the Firebase UID for mobile purchasers)

### Authenticated Endpoints (Sanctum)

```
POST   /api/v1/auth/logout         # Revoke current Sanctum token
GET    /api/v1/saved-jobs          # User's saved jobs
POST   /api/v1/saved-jobs          # Save a job
DELETE /api/v1/saved-jobs/{jobId}  # Unsave
GET    /api/v1/alerts              # User's alerts
POST   /api/v1/alerts              # Create alert
PUT    /api/v1/alerts/{id}         # Update alert
DELETE /api/v1/alerts/{id}         # Delete alert
```

### AI Tools API (API key required)

```
GET  /api/v1/tools                   # List all tools metadata
GET  /api/v1/tools/{slug}            # Single tool detail
POST /api/v1/tools/{slug}/generate   # Start generation (returns 202)
GET  /api/v1/generations/{id}        # Poll generation status/result
GET  /api/v1/generations             # User's generation history (auth:sanctum)
```

### Web Routes

```
GET  /tools                          # AI Tools gallery
GET  /tools/{slug}                   # Tool landing page + Livewire form
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

## Mobile App (ArchGee-MobileApp/)

> Full details in `AIGuidelines/mobile_app_guidelines.md`

- **Stack**: Kotlin Multiplatform + Compose Multiplatform (Android + iOS)
- **Architecture**: Clean Architecture (Presentation → Domain → Data) with MVVM per screen
- **DI**: Koin 4.x
- **Networking**: Ktor 3.x (consumes Laravel `/api/v1/` endpoints with `X-Api-Key` header) + `ktor-client-auth` for automatic Sanctum token refresh
- **API Config**: `BuildConfig.ARCHGEE_API_BASE_URL` + `BuildConfig.ARCHGEE_API_KEY` (set in `local.properties`)
- **Database**: Room (cross-platform via BundledSQLiteDriver, current version: 4, destructive migration)
- **Auth**: Firebase Auth (anonymous + Google/Apple OAuth) → Sanctum bridge via `POST /api/v1/auth/firebase`. Ktor Auth plugin auto-refreshes expired Sanctum tokens by re-exchanging Firebase ID token. **Global 401 interceptor** in `HttpClientFactory.default` (`HttpResponseValidator`) detects truly-logged-out 401s (no Firebase user + no Sanctum token) and fires `AppGlobalUiState.requireSignIn()` — `MainScreenRoute` observes this and routes to `SignInScreenRoute`. Sign-in screen has Google + Apple + **Continue as guest** (anonymous Firebase). Logout button on home menu wipes local data via `JobRepository.clearLocalData()` and routes back to sign-in.
- **Monetization**: RevenueCat (subscriptions: free 4 swipes/day, premium unlimited; credits: consumable IAP for AI tools)
- **Navigation**: Jetpack Navigation Compose with `@Serializable` type-safe routes
- **Design System**: Separate `designsystem/` module with 40+ reusable composables
- **Package**: `com.measify.archgee` (layers: `presentation/`, `domain/`, `data/`, `util/`)

### Key Conventions (Kotlin/KMP)

- **MVVM pattern**: `ScreenRoute` + `UiStateHolder` + `StateFlow<UiState>` + sealed `UiEvent`
- **Domain models**: Pure `data class`, no serialization annotations, no platform types
- **Repositories**: Concrete classes (no interfaces unless needed), wrap results in `Result<T>`
- **API services**: Return raw types (no `Result`), let exceptions propagate to repositories
- **Response DTOs**: Must have `Dto`/`Response` suffix, include `toDomain()` mapping method
- **Request DTOs**: Must have `Request` suffix, use `@Serializable` + `@SerialName`
- **Coroutines**: Inject dispatchers, use `BackgroundExecutor` for IO, avoid `GlobalScope`
- **No pass-through use cases**: Call repositories directly from ViewModels unless orchestration needed
- **API error handling**: Always check `response.status.isSuccess()` before calling `.body()` — non-2xx responses (401, 402, etc.) must be handled first, parse `ErrorResponse` for message, then throw. See `RealCreditApiService.addCredits()` as reference pattern

### Mobile Design System Rules

The `designsystem/` module contains all reusable UI components. **Always use design system components instead of raw Material3 equivalents** in presentation screens:

| Instead of (raw Material3) | Use (design system) |
|---------------------------|---------------------|
| `Button` | `AppButton(style = PRIMARY)` |
| `OutlinedButton` | `AppButton(style = ALTERNATIVE)` |
| `TextButton` | `AppButton(style = TEXT)` |
| `TextButton` (destructive/delete) | `AppButton(style = DESTRUCTIVE)` |
| `Card` / `CardDefaults` | `AppCardContainer` |
| `CircularProgressIndicator` (standalone) | `LoadingProgress()` or `LoadingProgress(mode = CIRCULAR)` |
| `CircularProgressIndicator` (in button) | `AppButton(isLoading = true)` |
| Raw `Dialog` | `AppDialog` (info/error) or `AppModalBottomSheet` (content-heavy) |

**Key design system components** (`designsystem/src/commonMain/kotlin/.../components/`):

- **AppButton** — styles: `PRIMARY`, `ALTERNATIVE`, `TEXT`, `DESTRUCTIVE` (error-colored); sizes: `LARGE`/`MEDIUM`/`SMALL`/`EXTRA_SMALL`; supports `isLoading`, `startIcon`, `endIcon`
- **AppCardContainer** — generic card with `shape`, `backgroundColor`, `onClick`, `contentPaddingValues`
- **AppDialog** — types: `INFO`, `ERROR`; with title, body, confirm/dismiss buttons
- **AppModalBottomSheet** — bottom sheet with title, content slot, optional buttons (`hideButtons = true` for close-icon mode)
- **LoadingProgress** — modes: `CIRCULAR`, `OVERLAY`, `FULLSCREEN`
- **EmptyContentView** — empty state with animated illustration, title, text, optional action button
- **AppToolbar** — top app bar with navigation icon, title, actions
- **Chip** — styles: `FILLED`/`SECONDARY`/`OUTLINE`/etc., sizes: `LARGE`/`MEDIUM`/`SMALL`
- **UserInput** — custom text field (for simple inputs; use `OutlinedTextField` when labels/supportingText/dropdowns are needed)
- **CircularActionButton** — circular icon button with optional label text
- **MenuBottomSheet** — menu-style bottom sheet with grouped items
- **ShimmerBox** — animated shimmer placeholder for loading images/content; use with `SubcomposeAsyncImage(loading = { ShimmerBox(...) })`

**UX rules for modals:**
- `ModalBottomSheet` renders above the Scaffold — Snackbar/toast from `AppGlobalUiState` will be hidden behind it. Dismiss the sheet before showing toast messages (set `selectedItem = null` before calling `showUiMessage`)
- Images inside `AppModalBottomSheet` must have `heightIn(max = 400.dp)` to prevent tall images from pushing buttons off-screen

**Exceptions** (OK to use raw Material3):
- `OutlinedTextField` with labels/supportingText — `UserInput` doesn't support these
- `ExposedDropdownMenuBox` — no design system equivalent
- Inline small indicators inside custom layouts where `LoadingProgress` is too large

### Build Commands

```bash
./gradlew :composeApp:assembleDebug          # Android debug APK
./gradlew :composeApp:testDebugUnitTest      # Shared unit tests
# iOS: Build via Xcode only (slow — skip during routine validation)
```

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
- **Sitemap**: `spatie/laravel-sitemap` — includes static routes, jobs, categories, locations (country/city), blog posts, blog categories, AI tools. In Docker: writes to `storage/app/public/` (shared volume), served via Caddy rewrite `/sitemap.xml` → `/storage/sitemap.xml`
- **robots.txt**: Generated alongside sitemap. Disallows /admin, /dashboard, /api, /checkout, /horizon, /telescope. Includes AI crawler rules (GPTBot, ClaudeBot, PerplexityBot, GoogleOther). In Docker: same shared volume + Caddy rewrite pattern

### GEO — AI Search Visibility (Generative Engine Optimization)

- **`/llms.txt`**: Machine-readable site description for AI crawlers (follows [llmstxt.org](https://llmstxt.org/) spec). Route in `web.php`, template at `resources/views/seo/llms-txt.blade.php`. Lists categories, tools, core pages.
- **AI crawler rules**: robots.txt explicitly allows GPTBot, ClaudeBot, PerplexityBot, GoogleOther
- **FAQ schema**: `FAQPage` JSON-LD on homepage, category pSEO pages, country pSEO pages, and AI tool detail pages — provides citation hooks for AI search engines
- **Organization schema**: `Organization` JSON-LD on homepage for entity identity in Knowledge Graph
- **Tool schemas**: `SoftwareApplication` + `BreadcrumbList` + `FAQPage` on each tool detail page

### pSEO (Programmatic SEO)

- **Category pages**: `/jobs/category/{slug}` — FAQ schema, `seo_content` column for unique intro (editable in Filament admin), top countries cross-links
- **Country pages**: `/jobs/location/{country}` — FAQ schema, city chips, other-countries sidebar
- **City pages**: `/jobs/location/{country}/{city}` — breadcrumbs linking to country page
- **Countries**: All ~248 ISO 3166-1 alpha-2 countries supported via `app/Constants/Countries.php`. Names come from PHP `intl` (`Locale::getDisplayRegion`), flags from Unicode regional-indicator pairs. No artificial whitelist — pSEO routes and the country filter dropdown work for any real ISO code. `JobsController::resolveCountryName()` delegates to `Countries::name()`.
- **`seo_content`**: Nullable text column on `job_categories` table — admin-editable unique content per category to avoid thin pages

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

## AI Tools System

Modular system for AI-powered design tools (interior redesign, sketch-to-render, etc.) using Replicate API.

### Architecture

```
User → POST /api/v1/tools/{slug}/generate (or Livewire submit)
  → GenerationService.create() → AIGeneration (QUEUED) → dispatch RunAIToolJob
  → Queue worker: RunAIToolJob
    → ToolRegistry.findOrFail(slug) → BaseTool config
    → ReplicateService.startPrediction() → poll → download output
    → AIGeneration (COMPLETED)
  → User polls: GET /api/v1/generations/{id} or wire:poll.3s
```

### Tool Abstraction (`app/AI/Tools/`)

- `BaseTool` — abstract class: `slug()`, `name()`, `description()`, `tagline()`, `ctaLabel()`, `steps()`, `icon()`, `replicateModel()`, `inputSchema()`, `buildReplicatePayload()`, `extractOutputUrl()`
- `InteriorDesignerTool` — room photo → redesigned space (Replicate model: `adirik/interior-design`)
- `SketchToDesignTool` — sketch → photorealistic render (configurable default model)
- `ToolRegistry` — singleton, auto-discovers tools by scanning `app/AI/Tools/` for `BaseTool` subclasses

### Adding a New Tool (3 files)

1. `app/AI/Tools/NewTool.php` — extends `BaseTool` (slug, name, inputs, Replicate model, payload builder)
2. `app/Livewire/Tools/NewTool.php` — extends `BaseToolComponent` (properties, `getTool()`, `collectInputs()`)
3. `resources/views/livewire/tools/new-tool.blade.php` — tool-specific form UI

Everything else (gallery, API endpoints, queue job, admin panel, status polling) works automatically.

### Replicate Config

```env
REPLICATE_API_KEY=r8_...
REPLICATE_DEFAULT_MODEL=owner/model:version
REPLICATE_POLL_TIMEOUT=300
REPLICATE_FREE_DAILY_LIMIT=3
```

### File Storage (Cloudflare R2)

AI tool inputs and outputs are stored on Cloudflare R2 (S3-compatible), not on local disk. This allows the `app` and `horizon` Docker containers to share files without shared volumes.

```env
CLOUDFLARE_R2_ACCESS_KEY_ID=...
CLOUDFLARE_R2_SECRET_ACCESS_KEY=...
CLOUDFLARE_R2_BUCKET=archgee-ai-tools
CLOUDFLARE_R2_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
CLOUDFLARE_R2_URL=https://<PUBLIC_URL>   # R2.dev subdomain or custom domain
```

- **Inputs** (`ai-tools/inputs/`): Private — stored on upload, read by queue job as base64, cleaned up after 24h
- **Outputs** (`ai-tools/outputs/{id}/`): Public — served via `CLOUDFLARE_R2_URL`, cleaned up after 24h
- **Disk name**: `r2` (configured in `config/filesystems.php`)
- **Used by**: `GenerationService` (store input), `RunAIToolJob` (read input, store output via `ReplicateService`), `CleanupOldGenerationsCommand` (delete both), `AIGeneration::outputImageUrl()` (public URL)

### UI Design Pattern (Tool Pages)

- **Landing page** (`tools/show.blade.php`): stone/neutral palette, centered hero with tagline + CTA, "how it works" 3-step section, Alpine.js staggered fade-in animations
- **Livewire forms**: 4 states (form → loading → error → result), stone-* neutral colors, `rounded-full` buttons, Alpine.js `x-transition` on state changes
- **Gallery** (`tools/index.blade.php`): dark hero, 3-column card grid with hover-lift animations

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

## Security Best Practices

When writing or reviewing code, always follow these security rules:

### Secret Comparison
- **Always use `hash_equals()`** for comparing secrets (API keys, tokens, hashes) — never `===` or `!==` (timing attack risk)

### Authorization (IDOR Prevention)
- **Always scope resource lookups by authenticated user ID** — never fetch a resource by ID alone without verifying ownership
- Use `$request->user()->id` to scope queries, not nullable user parameters that skip checks when null

### Input Validation
- **Always set `max` length** on all string/text validation rules to prevent payload abuse
- Sanitize user text before concatenating into AI/LLM prompts — strip control characters: `preg_replace('/[^\p{L}\p{N}\s.,!?\'-]/u', '', $input)`
- Validate and constrain all query parameters (length, type, allowed values)

### File Uploads
- **Never store user uploads on `public` disk** — use private disk and serve via signed URLs or auth-gated controllers
- Always validate MIME type (`mimes:jpeg,png,webp`), file size (`max:10240`), and extension

### API Security
- Use endpoint-specific rate limits for sensitive operations (`throttle:10,1` for auth, submit, generate)
- Set Sanctum token expiration (`config/sanctum.php`) — never allow infinite token lifetime
- Security headers middleware (`SecurityHeaders.php`) is globally registered — do not remove

### External Service Verification
- **Never return `true` as fallback** when external verification services (RevenueCat, etc.) are unconfigured — always fail closed
- Validate Replicate output URLs against allowed hostnames before downloading

### Logging
- Never log attacker-controlled values (forged token payloads, manipulated headers) — log the event type only
- Never log secrets, API keys, or full stack traces in production

### Configuration
- `.env.example` defaults to `APP_DEBUG=false` — always keep it that way
- Ensure `SESSION_SECURE_COOKIE=true` in production

## Blog Content System

SEO-driven blog for organic traffic growth. Markdown-based writing workflow with Artisan import into the existing SaaSykit blog system.

### Architecture

```
Write blog post as .mdx file (blog-content/posts/{slug}.mdx)
  → php artisan blog:import --all (or blog:import {slug})
  → Parse YAML frontmatter + convert Markdown → HTML
  → Post-process: wrap tables in .blog-table-wrapper, FAQ in accordion markup
  → Generate cover image (BlogCoverImageService → 1200x630 PNG)
  → Create/update BlogPost record in DB
  → Blog appears at /blog/{slug}
```

### File Format (`.mdx` with YAML frontmatter)

```markdown
---
title: "Architect Salary in London 2026: What to Expect"
slug: architect-salary-london
description: "Detailed look at architect salaries in London..."
category: "Careers & Salaries"
author: "ArchGee Editorial"
published_at: "2026-03-26"
keywords: ["architect salary london", "london architect pay"]
---

# Heading

Content with **bold**, tables, and internal links to [ArchGee](/jobs).

## FAQ

### Question here?

Answer paragraph here.
```

### Import Command

```bash
php artisan blog:import {slug}     # Import single post
php artisan blog:import --all      # Import all .mdx files (skips existing)
php artisan blog:import --all --force  # Import all, overwrite existing
```

- Auto-creates `BlogPostCategory` from frontmatter `category` field
- Generates cover image via `BlogCoverImageService` (dark bg, orange accents, white title)
- Attaches cover via Spatie Media Library `blog-images` collection
- Source `.mdx` files are **kept** after import (not deleted)
- Runs automatically on deploy via `entrypoint.sh` (skips already-imported posts)

### HTML Post-Processing

The import command post-processes converted HTML:
- **Tables**: Wrapped in `<div class="blog-table-wrapper">` for responsive scrolling + styled headers
- **FAQ sections**: `## FAQ` heading + `### Question` items converted to Alpine.js accordion with `x-data`, `x-show`, chevron rotation

### Writing Workflow

1. Check `blog-content/blog-topics.json` for next pending topic
2. Read `blog-content/blog-guidelines.md` for tone, structure, SEO rules
3. Write `.mdx` file in `blog-content/posts/{slug}.mdx`
4. Run `php artisan blog:import --all`
5. Update topic status to `"published"` in `blog-topics.json`

### Blog Guidelines Summary (`blog-content/blog-guidelines.md`)

- **Tone**: Expert architect/designer, human, slightly opinionated
- **Length**: 1,200-2,000 words
- **Structure**: SEO title → hook intro → H2/H3 sections with tables → FAQ → CTA
- **FAQ**: Every post must include 3-5 FAQs (`## FAQ` → `### Question?` → answer paragraph)
- **ArchGee mentions**: Max 2-3 per post, natural placements linking to `/jobs`, `/tools`
- **Quality**: Specific salary figures, real data, no filler, no AI-sounding phrases
- **Tables**: Use markdown tables for salary data — they get auto-styled on import
- **Categories**: Careers & Salaries, Location Guides, Remote Work, Career Growth, Industry Insights, Design & Architecture

### Topic Tracker (`blog-content/blog-topics.json`)

- 100 SEO topics with `status: "pending"` or `"published"`
- Organized by category with `primary_keyword` for each
- Check this file to find the next topic to write

### Blog Styling

Custom CSS in `resources/css/styles.css` under `article.blog-post`:
- Dark table headers with rounded wrapper, hover rows
- Accordion FAQ with Alpine.js (click to expand, chevron rotation)
- Strong heading hierarchy (orange bottom border on H2s)
- Cover images generated automatically (no manual image work needed)

### Key Files

| File | Purpose |
|------|---------|
| `app/Console/Commands/ImportBlogPostCommand.php` | MDX → DB import with post-processing |
| `app/Services/BlogCoverImageService.php` | Cover image generation (Intervention Image v3) |
| `blog-content/blog-guidelines.md` | Writing rules and SEO guidelines |
| `blog-content/blog-topics.json` | 100 topic tracker with status |
| `blog-content/posts/*.mdx` | Blog post source files |
| `resources/css/styles.css` | Blog-specific CSS (tables, FAQ accordion) |
| `resources/views/components/blog/post.blade.php` | Blog post detail template |
| `resources/views/components/blog/post-card.blade.php` | Blog listing card template |

## Medium Cross-Posting (semi-automated)

Drip-fed daily reminder system for cross-posting ArchGee blog posts to Medium while preserving SEO via canonical URLs.

### Why it's not fully automated

**Medium no longer issues new API integration tokens.** There is no legitimate way to `POST /v1/users/{id}/posts` unless you already hold a legacy token. Browser automation and scraped backdoors are explicitly rejected as fragile/ToS-risky. Instead, we use Medium's official [Import a post](https://help.medium.com/hc/en-us/articles/214550207) tool (`medium.com/p/import`) which **automatically sets the canonical link to the source URL** on import — which is exactly what cross-post SEO needs. The only manual step is ~30 seconds to paste the URL and click Import.

### Architecture

```
Scheduler (09:15 daily)  ──┐
                           ├──> MediumCrossPostService.dispatchNextReminder()
Filament button (manual) ──┘              │
                                           ▼
                              BlogPost::eligibleForMedium()->first()
                                           │
                                           ▼
                       Mail::to($recipient)->send(MediumCrossPostReminderMail)
                                           │
                                           ▼
                              Stamp medium_queued_at in DB transaction
```

Both triggers call the **same** `MediumCrossPostService` — scheduler and admin button share zero-duplication code paths.

### Data model (`blog_posts` table)

Migration `2026_04_10_000000_add_medium_columns_to_blog_posts_table.php` adds three nullable columns:

- `medium_queued_at` — set when the reminder email is dispatched
- `medium_published_at` — set when admin clicks the signed "mark as posted" link
- `medium_url` — validated Medium URL (must be `medium.com` or `*.medium.com`)

Also adds index `blog_posts_medium_eligible_idx` on `(is_published, medium_queued_at)`.

**Side fix:** the `BlogPost` model had no `$casts` array, so `published_at` was returned as a raw string. This crashed `/blog/{slug}` with `Call to a member function toIso8601String() on string`. Added `published_at`, `medium_queued_at`, `medium_published_at` → `datetime`, and `is_published` → `boolean`.

### Eligibility scope

```php
BlogPost::query()
    ->where('is_published', true)
    ->whereNotNull('published_at')
    ->whereNull('medium_queued_at')   // not yet notified
    ->orderBy('published_at');         // oldest first — natural backlog drain
```

Exposed as `BlogPost::scopeEligibleForMedium()`.

### Signed "mark as posted" URL

- Route: `blog.medium-posted` via `GET /admin/blog/{post}/medium-posted` with `signed` middleware
- TTL: 14 days (`MediumCrossPostService::MARK_POSTED_LINK_TTL_DAYS`)
- Optional `?medium_url=` query param — validated against `medium.com`/`*.medium.com` allowlist in `MediumCrossPostController::resolveMediumUrl()` (checks scheme, host, max length 500 chars)
- Rejects non-Medium URLs silently (stores null) to prevent the column from being used as an open-redirect vector
- Redirects to `filament.admin.resources.blog-posts.edit` on success

### Filament admin integration

`BlogPostResource`:
- **"Medium" column** — badge showing `Not queued` / `Reminded` / `Published`
- **"Medium Status" filter** — filter the list by one of those three states
- **Bulk action "Re-queue to Medium"** — clears `medium_queued_at` + `medium_published_at` so posts get picked up on the next run (for when the admin never actually imported)
- **Bulk action "Mark Medium posted"** — stamps both timestamps at `now()` (for historical backfill)
- **Edit form section "Medium Cross-Post"** — shows status string + clickable Medium URL

`ListBlogPosts` page:
- **Header action "Run Medium drip now"** — confirmation dialog, then calls `MediumCrossPostService.dispatchNextReminder()` (same code path as the scheduler), shows a Filament notification with the title of the queued post

### Configuration

`config/services.php`:

```php
'medium' => [
    'cross_post_recipient' => env('MEDIUM_CROSS_POST_RECIPIENT', env('ADMIN_EMAIL')),
],
```

Env var fallback chain: `MEDIUM_CROSS_POST_RECIPIENT` → `ADMIN_EMAIL` → null (errors out with clear message).

### Suggested Medium tags

Generated by `MediumCrossPostService::buildSuggestedTags()`:

1. Blog post's category name
2. Always "Architecture" + "Careers" (brand/niche baseline)
3. Up to 3 H2 headings parsed from the post's HTML body, truncated to 22 chars (Medium's 25-char cap)
4. "FAQ" heading skipped
5. Deduped, capped at Medium's 5-tag limit

### Failure semantics

- Mail dispatch fails → `medium_queued_at` **NOT** stamped → post stays eligible → picked up on next run
- DB update wrapped in `DB::transaction()` so the stamp is atomic
- Service throws `\RuntimeException` on missing recipient; CLI and Filament button both catch and surface the error

### Commands

```bash
# Dry-run — show what would be sent, no DB writes, no mail
./vendor/bin/sail artisan blog:cross-post-to-medium --dry-run

# Real run — picks next eligible post, sends reminder, stamps queued_at
./vendor/bin/sail artisan blog:cross-post-to-medium
```

Schedule: `Schedule::command('blog:cross-post-to-medium')->dailyAt('09:15')->withoutOverlapping()->onOneServer();`

### Upgrade path if a Medium API token ever appears

Add a `sendToMediumApi(BlogPost $post): string` method to `MediumCrossPostService` that POSTs to `https://api.medium.com/v1/users/{userId}/posts` with the post's markdown body + `canonicalUrl` field set to the ArchGee URL. Switch `dispatchNextReminder()` to call it instead of sending the email, and stamp `medium_published_at` directly. Command, scheduler, Filament button, and admin panel all continue working without changes.

### Key files

| File | Purpose |
|------|---------|
| `database/migrations/2026_04_10_000000_add_medium_columns_to_blog_posts_table.php` | Adds the three Medium columns + index |
| `app/Services/MediumCrossPostService.php` | Single source of truth — `dispatchNextReminder()` + `previewNextReminder()` + tag builder |
| `app/Console/Commands/CrossPostToMediumCommand.php` | Thin wrapper around the service, supports `--dry-run` |
| `app/Mail/MediumCrossPostReminderMail.php` | Queued mailable |
| `resources/views/emails/blog/medium-cross-post-reminder.blade.php` | 3-step email template |
| `app/Http/Controllers/MediumCrossPostController.php` | `markPosted()` handler with Medium-hostname validation |
| `app/Models/BlogPost.php` | `scopeEligibleForMedium()` + datetime casts |
| `app/Filament/Admin/Resources/BlogPosts/BlogPostResource.php` | Column, filter, bulk actions, form section |
| `app/Filament/Admin/Resources/BlogPosts/Pages/ListBlogPosts.php` | "Run Medium drip now" header action |
| `routes/console.php` | Daily scheduler entry |
| `routes/web.php` | Signed route |
| `config/services.php` | `services.medium.cross_post_recipient` |

## Important References

- **Coding guidelines**: `ArchGee-Website/ai/laravel-php-ai-guidelines.md`
- **Boilerplate docs**: `ArchGee-Website/AGENTS.md` (SaaSykit original)
- **All guideline docs**: `AIGuidelines/` directory (PRD, schema, API, AI prompts, SEO, UI, sources, mobile app)
- **Mobile app guidelines**: `AIGuidelines/mobile_app_guidelines.md` (architecture, API integration, conventions)
- **Blog guidelines**: `ArchGee-Website/blog-content/blog-guidelines.md` (writing rules, SEO, tone, structure)
- **Blog topics**: `ArchGee-Website/blog-content/blog-topics.json` (100 SEO topics with status tracking)
