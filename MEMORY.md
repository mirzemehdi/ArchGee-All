# ArchGee Project Memory

## Project Overview
- **Name**: ArchGee - Architecture & Design Jobs Platform
- **Type**: Niche AI-powered job aggregation for built-environment professionals
- **Root**: `/Users/mirzemehdi/Documents/SAAS/ArchGee-All`
- **App**: `/Users/mirzemehdi/Documents/SAAS/ArchGee-All/ArchGee-Website` (Laravel app)
- **Guidelines**: `/Users/mirzemehdi/Documents/SAAS/ArchGee-All/AIGuidelines/`

## Stack
- **Foundation**: SaaSykit boilerplate (Laravel 12, PHP 8.2+)
- **Frontend**: TALL (Tailwind 4, Alpine.js, Laravel, Livewire 4) + DaisyUI 5
- **Admin**: Filament 5 (two panels: `/admin` + `/dashboard`)
- **DB**: MySQL 8.0 via Docker/Sail
- **Queue**: Laravel Horizon (Redis)
- **Auth**: Sanctum, Socialite, Filament Breezy
- **Search**: Laravel Scout (database driver default, Meilisearch ready)
- **AI**: OpenAI gpt-4o-mini (primary), Anthropic/Mistral fallback
- **Dev**: Docker Sail — always use `./vendor/bin/sail` for commands

## Key Conventions
- Follow `ai/laravel-php-ai-guidelines.md` for coding standards
- Service layer pattern for business logic
- Filament for admin UI, Livewire for interactive components
- Event-driven architecture for side effects
- Queue long-running tasks
- PSR-12, camelCase methods/vars, PascalCase classes
- UUIDs for job primary keys (public-facing)

## Job Board Architecture
```
Sources → POST /api/ingest/jobs → Normalization → AI Enrichment Queue → Moderation → Published
```
- No employer accounts — anyone can submit via public form
- Admin moderates all jobs (pending → approved/rejected)
- 4-stage AI pipeline: Relevance → Salary → Work Type → Seniority

## Guideline Files
- `AIGuidelines/prd.md` - Product Requirements Document (v1.1.0)
- `AIGuidelines/db_schema.md` - Normalized database schema
- `AIGuidelines/api_endpoints.md` - Full REST API specification
- `AIGuidelines/ai_prompts.md` - AI enrichment prompts and pipeline
- `AIGuidelines/scraper_guidelines.md` - Python scraper contract
- `AIGuidelines/seo_guidelines.md` - SEO/Google Jobs guidelines

## Key Files (Job Board - New)
- **Models**: `app/Models/Job.php`, `JobCategory.php`, `JobSource.php`, `JobTag.php`, `SavedJob.php`, `JobAlert.php`, `JobApplicationClick.php`
- **Enums**: `app/Constants/JobStatus.php`, `RemoteType.php`, `SeniorityLevel.php`, `EmploymentType.php`, `SalaryPeriod.php`, `JobSourceType.php`, `AlertFrequency.php`
- **Services**: `app/Services/JobService.php`, `app/Services/AiEnrichmentService.php`
- **Queue Jobs**: `app/Jobs/EnrichJobWithAi.php`
- **API Controllers**: `app/Http/Controllers/Api/JobIngestController.php`, `Api/V1/JobController.php`, `Api/V1/CategoryController.php`, `Api/V1/SavedJobController.php`
- **API Resources**: `app/Http/Resources/JobListResource.php`, `JobDetailResource.php`
- **Web Controller**: `app/Http/Controllers/JobsController.php`
- **Livewire**: `app/Livewire/Jobs/PostJobForm.php`
- **Filament Admin**: `app/Filament/Admin/Resources/Jobs/`, `JobCategories/`, `JobSources/`
- **Views**: `resources/views/jobs/index.blade.php`, `show.blade.php`, `post.blade.php`
- **Livewire Views**: `resources/views/livewire/jobs/post-job-form.blade.php`
- **Migrations**: `database/migrations/2026_02_18_000001` through `000007`
- **Seeders**: `database/seeders/JobCategoriesSeeder.php`, `JobSourcesSeeder.php`
- **Commands**: `app/Console/Commands/ExpireOldJobsCommand.php`

## External Resources
- Job board features: https://www.jobboardly.com/
- Post job UI reference: https://androidjobs.io/jobs/new
- Python scraper inspiration: https://github.com/speedyapply/JobSpy
- SaaSykit docs: https://saasykit.com/docs/
