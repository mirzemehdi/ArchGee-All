# ArchGee - Developer Setup Guide

## Prerequisites
- Docker Desktop installed and running
- Node.js 18+ (for local npm if needed)
- An OpenAI API key (for AI enrichment — optional for basic functionality)

---

## 1. Start Docker Sail

```bash
cd ArchGee-Website

# Start all containers (MySQL, Redis, Mailpit, Ngrok)
./vendor/bin/sail up -d
```

**What this starts:**
| Service | Port | URL |
|---------|------|-----|
| Laravel App | 8080 | http://localhost:8080 |
| MySQL 8.0 | 3306 | `mysql` host inside Docker |
| Redis | 6379 | `redis` host inside Docker |
| Mailpit (email) | 8025 | http://localhost:8025 |
| Ngrok | 4040 | http://localhost:4040 |

---

## 2. Install Dependencies & Setup Database

```bash
# Install PHP dependencies (if not already done)
./vendor/bin/sail composer install

# Install Node dependencies
./vendor/bin/sail npm install

# Run all migrations
./vendor/bin/sail artisan migrate

# Seed the database (categories, sources, roles, etc.)
./vendor/bin/sail artisan db:seed

# OR fresh install (drops all tables and re-seeds)
./vendor/bin/sail artisan migrate:fresh --seed
```

---

## 3. Create Admin User

```bash
./vendor/bin/sail artisan app:create-admin-user
```

Follow the prompts to create your admin account. Then login at http://localhost:8080/admin

---

## 4. Build Frontend Assets

```bash
# Development (hot reload)
./vendor/bin/sail npm run dev

# Production build
./vendor/bin/sail npm run build
```

---

## 5. Configure AI Enrichment (Optional)

The AI enrichment pipeline classifies jobs, extracts salaries, and detects work type / seniority. It requires an API key.

### Option A: OpenAI (Recommended)

1. Get an API key from https://platform.openai.com/api-keys
2. Edit `.env`:

```env
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
AI_API_KEY=sk-your-key-here
```

**Cost**: ~$0.001 per job (gpt-4o-mini is very cheap)

### Option B: Anthropic Claude

1. Get an API key from https://console.anthropic.com/
2. Edit `.env`:

```env
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-haiku-20241022
AI_API_KEY=sk-ant-your-key-here
```

### Without AI Key

The platform works without an AI key. Jobs will be ingested but won't be auto-classified. You'll need to manually set categories, seniority, etc. in the Filament admin panel.

---

## 6. Configure Search (Optional)

By default, search uses the **database driver** (MySQL LIKE queries). For better search, configure Meilisearch:

### Install Meilisearch

Add to your `docker-compose.yml`:
```yaml
meilisearch:
    image: 'getmeili/meilisearch:latest'
    ports:
        - '${FORWARD_MEILISEARCH_PORT:-7700}:7700'
    environment:
        MEILI_MASTER_KEY: '${MEILISEARCH_KEY:-masterKey}'
    volumes:
        - 'sail-meilisearch:/meili_data'
    networks:
        - sail
```

Add to volumes section:
```yaml
sail-meilisearch:
    driver: local
```

Then install the PHP packages:
```bash
./vendor/bin/sail composer require laravel/scout meilisearch/meilisearch-php
```

Update `.env`:
```env
SCOUT_DRIVER=meilisearch
MEILISEARCH_HOST=http://meilisearch:7700
MEILISEARCH_KEY=masterKey
```

Import existing jobs:
```bash
./vendor/bin/sail artisan scout:import "App\Models\Job"
```

---

## 7. Create a Scraper API Token

To allow external scrapers to ingest jobs:

```bash
./vendor/bin/sail artisan tinker
```

```php
$user = \App\Models\User::where('is_admin', true)->first();
$token = $user->createToken('scraper', ['ingest:jobs']);
echo $token->plainTextToken;
```

Save this token. Use it in scraper configs:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

---

## 8. Key URLs

| Page | URL |
|------|-----|
| Home | http://localhost:8080 |
| Job Listings | http://localhost:8080/jobs |
| Post a Job | http://localhost:8080/jobs/post |
| Admin Panel | http://localhost:8080/admin |
| User Dashboard | http://localhost:8080/dashboard |
| Horizon (Queues) | http://localhost:8080/horizon |
| Telescope (Debug) | http://localhost:8080/telescope |
| Mailpit (Emails) | http://localhost:8025 |

---

## 9. Running Tests

```bash
# Run all tests
./vendor/bin/sail test

# Run specific test
./vendor/bin/sail test --filter=JobTest

# With coverage
./vendor/bin/sail test --coverage
```

**Important**: Tests use the `testing` database (auto-created by Docker). The `.env.testing` file is configured to use `DB_HOST=mysql` and `DB_DATABASE=testing`.

---

## 10. Queue Processing

For the AI enrichment pipeline and other background tasks:

```bash
# Start Horizon (recommended - monitors all queues)
./vendor/bin/sail artisan horizon

# Or simple queue worker
./vendor/bin/sail artisan queue:work
```

**Note**: By default, `QUEUE_CONNECTION=sync` in `.env`, which means jobs run synchronously (good for development). For async processing, change to:

```env
QUEUE_CONNECTION=redis
```

---

## 11. Scheduled Tasks

The app has a scheduled command to expire old jobs:

```bash
# Run manually
./vendor/bin/sail artisan jobs:expire-old

# For production, add to cron:
# * * * * * cd /path-to-project && php artisan schedule:run >> /dev/null 2>&1
```

---

## 12. API Endpoints Quick Reference

### Public (no auth)
- `GET /api/v1/jobs` — List jobs with filters
- `GET /api/v1/jobs/{slug}` — Job detail
- `GET /api/v1/categories` — List categories
- `POST /api/v1/jobs/submit` — Submit a job (public form)

### Authenticated (Sanctum token)
- `GET /api/v1/saved-jobs` — List saved jobs
- `POST /api/v1/saved-jobs` — Save a job
- `DELETE /api/v1/saved-jobs/{jobId}` — Unsave

### Scraper Ingest (Sanctum token)
- `POST /api/ingest/job` — Single job
- `POST /api/ingest/jobs` — Bulk (up to 100)

See `AIGuidelines/api_endpoints.md` for full documentation.

---

## Troubleshooting

### "mysql: getaddrinfo failed"
You're running artisan commands outside Docker. Use `./vendor/bin/sail artisan` instead of `php artisan`.

### "Table already exists" on migrate
Run `./vendor/bin/sail artisan migrate:fresh --seed` to start clean.

### "Class not found" errors
Run `./vendor/bin/sail composer dump-autoload`.

### Filament admin shows 403
Make sure your user has `is_admin = true`. Check via tinker:
```php
$user = \App\Models\User::find(1);
$user->is_admin = true;
$user->save();
```

### AI enrichment not working
1. Check `AI_API_KEY` is set in `.env`
2. Check queue is running (`./vendor/bin/sail artisan horizon`)
3. Check `QUEUE_CONNECTION=redis` (not `sync` for background)
4. Check logs: `./vendor/bin/sail artisan log:tail` or `storage/logs/laravel.log`
