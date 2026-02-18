# ArchGee AI Enrichment Prompts

## Overview
AI enrichment runs as queued jobs after a job is ingested. Each enrichment step is a separate queue job for modularity and retry isolation. The pipeline uses OpenAI (primary), with Anthropic and Mistral as fallbacks.

## Configuration
```env
AI_PROVIDER=openai          # openai | anthropic | mistral
AI_MODEL=gpt-4o-mini        # model identifier
AI_API_KEY=sk-...
AI_TEMPERATURE=0.1          # low temperature for deterministic classification
AI_MAX_RETRIES=3
AI_RELEVANCE_THRESHOLD=0.6  # minimum score to auto-approve for moderation
```

---

## Pipeline Stages

### Stage 1: Relevance Classification
Determines if a job is relevant to architecture/built-environment and assigns a category.

**Queue Job**: `App\Jobs\ClassifyJobRelevance`

**System Prompt**:
```
You are a job classification engine for ArchGee, a job platform exclusively for built-environment professionals (architects, interior designers, landscape architects, urban designers, urban planners, BIM specialists, sustainability consultants, heritage consultants).

Evaluate the job title and description. Determine:
1. Whether this job is relevant to the built-environment profession
2. Which category best fits

Return ONLY valid JSON, no explanation.
```

**User Prompt**:
```
Job Title: {{title}}
Company: {{company}}
Job Description (first 2000 chars): {{description}}

Return JSON:
{
  "relevant": true|false,
  "category_slug": "architect|interior-designer|landscape-architect|urban-designer|urban-planner|bim-specialist|project-manager|sustainability-consultant|heritage-consultant|other",
  "confidence": 0.0-1.0,
  "reasoning": "One sentence explanation"
}
```

**Business Rules**:
- If `relevant == false` → auto-set status to `rejected`
- If `relevant == true && confidence >= 0.8` → keep `pending` for moderation
- If `relevant == true && confidence < 0.6` → flag for manual review
- Save `ai_relevance_score` and `ai_category_confidence` on the job

---

### Stage 2: Salary Extraction
Extracts structured salary data from job descriptions.

**Queue Job**: `App\Jobs\ExtractJobSalary`

**System Prompt**:
```
You are a salary extraction engine. Extract salary information from job postings. If no salary is mentioned, return nulls. Normalize all salaries to annual amounts when possible. Handle various formats: "$60k-80k", "£45,000 per annum", "€3,500/month", "$35-45/hr".
```

**User Prompt**:
```
Job Title: {{title}}
Job Description: {{description}}

Return ONLY valid JSON:
{
  "salary_min": number|null,
  "salary_max": number|null,
  "salary_currency": "USD"|"EUR"|"GBP"|"AUD"|"CAD"|"AED"|"SGD"|null,
  "salary_period": "year"|"month"|"hour"|null,
  "salary_normalized_annual_min": number|null,
  "salary_normalized_annual_max": number|null
}

Rules:
- Convert "k" notation: 60k = 60000
- If only one salary given, use it for both min and max
- For hourly: annual = hourly × 2080
- For monthly: annual = monthly × 12
- Currency detection: $=USD, £=GBP, €=EUR, A$=AUD, C$=CAD, AED=AED
```

---

### Stage 3: Work Type Detection
Determines remote/hybrid/onsite status.

**Queue Job**: `App\Jobs\DetectJobWorkType`

**System Prompt**:
```
You are a work type classifier. Determine whether a job is remote, hybrid, or onsite based on the job posting content.
```

**User Prompt**:
```
Job Title: {{title}}
Location: {{location_text}}
Job Description (first 1500 chars): {{description}}

Return ONLY valid JSON:
{
  "remote_type": "remote"|"hybrid"|"onsite",
  "confidence": 0.0-1.0
}

Rules:
- "Work from home", "remote-first", "fully remote", "anywhere" → remote
- "Hybrid", "2 days in office", "flexible location" → hybrid
- Physical address only, "on-site", "in-office" → onsite
- Default to "onsite" if unclear
```

---

### Stage 4: Seniority Detection
Determines the seniority level.

**Queue Job**: `App\Jobs\DetectJobSeniority`

**System Prompt**:
```
You are a seniority level classifier for architecture and design jobs. Determine the seniority level from the job title and description.
```

**User Prompt**:
```
Job Title: {{title}}
Job Description (first 1500 chars): {{description}}

Return ONLY valid JSON:
{
  "seniority_level": "intern"|"junior"|"mid"|"senior"|"lead"|"principal"|"director",
  "confidence": 0.0-1.0
}

Rules:
- "Intern", "placement", "graduate" → intern
- "Junior", "Part I", "Part 1", "entry level", "0-2 years" → junior
- "Architect", "Designer" (no qualifier), "3-5 years" → mid
- "Senior", "Part III", "Part 3", "5+ years" → senior
- "Lead", "Team Leader", "Associate Director" → lead
- "Principal", "Partner" → principal
- "Director", "Head of", "VP" → director
- Architecture-specific: Part I = junior, Part II = mid, Part III = senior
```

---

## Implementation Notes

### Service Class: `App\Services\AiEnrichmentService`

```php
class AiEnrichmentService
{
    public function classifyRelevance(Job $job): array;
    public function extractSalary(Job $job): array;
    public function detectWorkType(Job $job): array;
    public function detectSeniority(Job $job): array;
    public function enrichJob(Job $job): void; // runs all stages
}
```

### Queue Chain
After job creation, dispatch the chain:
```php
ClassifyJobRelevance::dispatch($job)
    ->chain([
        new ExtractJobSalary($job),
        new DetectJobWorkType($job),
        new DetectJobSeniority($job),
    ]);
```

If Stage 1 marks as irrelevant, the chain should stop (no need to process further).

### Error Handling
- Each stage retries up to 3 times with exponential backoff
- On final failure, mark job as `needs_review` and log the error
- AI API errors should not block the moderation queue
- Store raw AI responses in a `job_ai_logs` table for debugging (optional Phase 2)

### Cost Management
- Use `gpt-4o-mini` for all classification (cheap, fast)
- Truncate descriptions to 2000 chars to reduce token usage
- Batch process during off-peak hours for large imports
- Cache common patterns to avoid redundant API calls
