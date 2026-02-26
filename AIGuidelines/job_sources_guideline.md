# ArchGee Job Sources Guideline

## Overview

ArchGee aggregates architecture and built-environment jobs from multiple external APIs. Each source has a dedicated FetchService, artisan command, and admin panel integration.

All sources run on a **6-hour schedule** and can also be triggered manually from the admin panel (**Sources > Import Jobs**).

---

## Integrated Sources (Tier 1 — Safe, Free, Official APIs)

### 1. Adzuna

| | |
|---|---|
| **Status** | Integrated |
| **API Docs** | https://developer.adzuna.com/ |
| **Auth** | App ID + App Key |
| **Rate Limits** | 25 requests/min, 250 requests/day (free tier) |
| **Coverage** | 16 countries (GB, US, AU, CA, DE, FR, IN, NL, NZ, SG, ZA, AT, BR, IT, PL) |
| **Arch Coverage** | Moderate — keyword-based filtering |
| **Pricing** | Free tier available |
| **ToS** | Designed for aggregation partners. Requires attribution. |

**Setup:**
```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

**Get credentials:** Register at https://developer.adzuna.com/

**CLI:**
```bash
php artisan jobs:fetch-adzuna --all-countries
php artisan jobs:fetch-adzuna --country=gb,us --max=50
php artisan jobs:fetch-adzuna --keywords="architect,BIM" --max=200
```

**Service:** `App\Services\AdzunaFetchService`
**Command:** `App\Console\Commands\FetchAdzunaJobsCommand`

---

### 2. Reed.co.uk

| | |
|---|---|
| **Status** | Integrated |
| **API Docs** | https://www.reed.co.uk/developers |
| **Auth** | API Key (Basic Auth) |
| **Rate Limits** | 1,000 requests/day |
| **Coverage** | UK only |
| **Arch Coverage** | Strong — ~2,500 architecture + ~10,000 construction jobs |
| **Pricing** | Free |
| **ToS** | Official API. Attribution required. |

**Setup:**
```env
REED_API_KEY=your_api_key
```

**Get credentials:** Register at https://www.reed.co.uk/developers — API key is provided immediately after signup.

**CLI:**
```bash
php artisan jobs:fetch-reed
php artisan jobs:fetch-reed --keywords="architect" --max=200
php artisan jobs:fetch-reed --location=London --distance=25
```

**Service:** `App\Services\ReedFetchService`
**Command:** `App\Console\Commands\FetchReedJobsCommand`

---

### 3. Careerjet

| | |
|---|---|
| **Status** | Integrated |
| **API Docs** | https://www.careerjet.com/partners/api |
| **Auth** | API Key (Basic HTTP auth — key as username, empty password) |
| **Rate Limits** | 1,000 requests/hour (can be increased) |
| **Coverage** | 16 locales (en_GB, en_US, en_AU, en_CA, de_DE, fr_FR, en_NZ, en_SG, en_ZA, en_AE, en_IN, nl_NL, it_IT, pl_PL, en_IE, en_HK) |
| **Arch Coverage** | Moderate — aggregates from many sources globally |
| **Pricing** | Free (affiliate/revenue-share model ~20% commission per click) |
| **ToS** | Must use tracking URLs (affiliate model). Partner account required. |

**Setup:**
```env
CAREERJET_API_KEY=your_api_key
```

**Get credentials:** Register as a partner at https://www.careerjet.com/partners/api

**Important:** Careerjet operates on an affiliate model. Job URLs returned are tracking URLs. Users clicking through generate revenue. **You must use the provided URLs as-is** (no redirecting or rewriting).

**CLI:**
```bash
php artisan jobs:fetch-careerjet --all-locales
php artisan jobs:fetch-careerjet --locale=en_GB,en_US --max=50
```

**Service:** `App\Services\CareerjetFetchService`
**Command:** `App\Console\Commands\FetchCareerjetJobsCommand`

---

### 4. Jooble

| | |
|---|---|
| **Status** | Integrated |
| **API Docs** | https://jooble.org/api/about |
| **Auth** | API Key |
| **Rate Limits** | Not publicly documented; reportedly generous |
| **Coverage** | 13 countries (GB, US, AU, CA, DE, FR, IN, NL, NZ, SG, ZA, AE, IE) |
| **Arch Coverage** | Moderate — aggregates from 140,000+ sources across 69 countries |
| **Pricing** | Free |
| **ToS** | Official API for publishers. Requires attribution/linking back. |

**Setup:**
```env
JOOBLE_API_KEY=your_api_key
```

**Get credentials:** Register at https://jooble.org/api/about — API key provided after signup.

**Note:** Jooble uses POST requests with country-specific subdomains (e.g., `au.jooble.org`, `de.jooble.org`). Returns 20 results per page by default.

**CLI:**
```bash
php artisan jobs:fetch-jooble --all-countries
php artisan jobs:fetch-jooble --country=gb,us --max=50
php artisan jobs:fetch-jooble --keywords="landscape architect"
```

**Service:** `App\Services\JoobleFetchService`
**Command:** `App\Console\Commands\FetchJoobleJobsCommand`

---

## Scheduler

All fetchers run every 6 hours (defined in `routes/console.php`):

```php
Schedule::command('jobs:fetch-adzuna', ['--all-countries'])->everySixHours()->withoutOverlapping();
Schedule::command('jobs:fetch-reed')->everySixHours()->withoutOverlapping();
Schedule::command('jobs:fetch-careerjet', ['--all-locales'])->everySixHours()->withoutOverlapping();
Schedule::command('jobs:fetch-jooble', ['--all-countries'])->everySixHours()->withoutOverlapping();
```

Each command uses `withoutOverlapping()` to prevent concurrent runs.

---

## Admin Panel

**Sources > Import Jobs** button opens a modal where you can:
1. Select a source (Adzuna, Reed, Careerjet, Jooble)
2. Modify keywords, max jobs, and country/locale selection
3. Trigger the fetch immediately

Each source row also has a **Fetch** button that opens the same modal pre-scoped to that source.

---

## Pipeline

Every job from every source goes through the same pipeline:

```
External API → FetchService → isDuplicate() check → createFromIngest() → EnrichJobWithAi queue
```

1. **Fetch** — Service calls external API with pagination
2. **Deduplicate** — `source_job_id` checked against existing jobs from the same source
3. **Ingest** — Job created with status `PENDING`
4. **AI Enrichment** — Queued job classifies relevance, extracts salary, detects work type + seniority
5. **Admin Review** — Admin approves or rejects

---

## Adding a New Source

To add a new source:

1. **Create service** — `app/Services/{Name}FetchService.php` following existing patterns
2. **Create command** — `app/Console/Commands/Fetch{Name}JobsCommand.php`
3. **Add config** — Add API keys to `config/services.php` and `.env`
4. **Register scheduler** — Add to `routes/console.php`
5. **Update admin panel** — Add to the source select in `ListJobSources.php` and the `match` statements
6. **Update per-row action** — Add slug to the `in_array()` check and `match` in `JobSourceResource.php`

---

## Future Sources (Tier 2 — Consider if Needed)

### The Muse
- **API:** https://www.themuse.com/developers/api/v2
- **Free:** Yes (3,600 req/hr with key)
- **Coverage:** Low for architecture — focuses on tech/business
- **Worth it?** Only if you want design-adjacent roles at large companies

### Arbeitnow
- **API:** https://www.arbeitnow.com/api/job-board-api
- **Free:** Yes (no key required)
- **Coverage:** Low for architecture — European tech/remote focus
- **Worth it?** Minimal value for architecture niche

---

## Do NOT Use (Tier 5 — ToS Violations / Legal Risk)

| Source | Why Not |
|---|---|
| **Indeed** | Job Search API deprecated. Scraping explicitly prohibited. Legal enforcement history. |
| **LinkedIn** | No public job search API. Scraping prohibited. Aggressive legal enforcement. |
| **Glassdoor** | API partnership discontinued. Scraping prohibited. |
| **Google Jobs** | No read API exists. SerpApi (third-party scraper) is being sued by Google. |
| **ZipRecruiter** | Partner API only (requires formal approval). Scraping prohibited. |
| **JobSpy library** | Scrapes Indeed/LinkedIn/Glassdoor — inherits all their ToS risks. Not for production/commercial use. |

---

## Architecture-Specific Sources (Tier 4 — Partnership Outreach)

These are the most valuable sources for ArchGee's niche but have no public APIs. The recommended approach is **direct partnership outreach** — offer mutual benefit (you drive traffic back, they get wider distribution).

| Source | Website | Why Valuable |
|---|---|---|
| **Archinect** | archinect.com/jobs | Premier architecture job board since 1997. ~150 jobs/week. |
| **Dezeen Jobs** | dezeenjobs.com | Top architecture/design job board globally. |
| **RIBA Jobs** | jobs.architecture.com | Royal Institute of British Architects — curated UK arch jobs. |
| **ArchDaily** | archdaily.com/jobs | World's largest architecture platform (13M+ monthly visits). |
| **Architizer** | architecture-jobs.architizer.com | Reaches 1M architects. Uses ZipRecruiter infrastructure. |

**Outreach template idea:**
> "We're building ArchGee, a niche job platform for architecture professionals. We'd love to explore a data partnership — your listings would reach our audience, and every job click links directly back to your site. Could we discuss an RSS feed or API arrangement?"

---

## Environment Variables Summary

```env
# Adzuna (16 countries)
ADZUNA_APP_ID=
ADZUNA_APP_KEY=

# Reed.co.uk (UK)
REED_API_KEY=

# Careerjet (16 locales, API key with Basic auth)
CAREERJET_API_KEY=

# Jooble (13 countries)
JOOBLE_API_KEY=
```

---

## Rate Limit Awareness

| Source | Rate Limit | Our 6-hr Schedule Impact |
|---|---|---|
| Adzuna | 250 req/day | ~15 countries x ~2 pages each = ~30 req per run. Well within limits. |
| Reed | 1,000 req/day | ~2 pages per run. Well within limits. |
| Careerjet | 1,000 req/hour | ~16 locales x ~1 page each = ~16 req per run. Well within limits. |
| Jooble | Undocumented | ~13 countries x ~5 pages each = ~65 req per run. Should be fine. |

With 4 runs per day (every 6 hours), total daily API calls:
- Adzuna: ~120 requests/day (limit: 250)
- Reed: ~8 requests/day (limit: 1,000)
- Careerjet: ~64 requests/day (limit: 1,000/hour)
- Jooble: ~260 requests/day (no documented limit)

All well within safe thresholds.
