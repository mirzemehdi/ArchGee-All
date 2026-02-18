# ArchGee SEO & Google Jobs Guidelines

## Overview
SEO is critical for a job board. Google Jobs integration drives organic traffic by displaying job listings directly in Google search results.

---

## 1. Google Jobs (schema.org/JobPosting)

### Required Structured Data
Every approved job detail page must include a `<script type="application/ld+json">` block.

### Full Schema Template

```json
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "Senior Architect",
  "description": "<p>HTML-formatted job description</p>",
  "identifier": {
    "@type": "PropertyValue",
    "name": "ArchGee",
    "value": "job-uuid"
  },
  "datePosted": "2026-01-15",
  "validThrough": "2026-02-15T23:59:59Z",
  "employmentType": "FULL_TIME",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "Foster + Partners",
    "sameAs": "https://fosterandpartners.com",
    "logo": "https://archgee.com/logos/foster-partners.png"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "London",
      "addressRegion": "England",
      "addressCountry": "GB"
    }
  },
  "jobLocationType": "TELECOMMUTE",
  "applicantLocationRequirements": {
    "@type": "Country",
    "name": "GB"
  },
  "baseSalary": {
    "@type": "MonetaryAmount",
    "currency": "GBP",
    "value": {
      "@type": "QuantitativeValue",
      "minValue": 60000,
      "maxValue": 80000,
      "unitText": "YEAR"
    }
  },
  "directApply": false
}
```

### Field Mapping

| Schema.org Field | Job Model Field | Notes |
|-----------------|-----------------|-------|
| title | title | Raw title, no company name prefix |
| description | description_html | Must be HTML, not plain text |
| datePosted | posted_at | ISO 8601 date |
| validThrough | expires_at | ISO 8601 datetime. Required by Google |
| employmentType | employment_type | Map: full_time→FULL_TIME, part_time→PART_TIME, contract→CONTRACTOR, freelance→CONTRACTOR, internship→INTERN |
| hiringOrganization.name | company_name | |
| hiringOrganization.sameAs | company_website | Only if available |
| jobLocation.address.addressLocality | city | |
| jobLocation.address.addressCountry | country | ISO 3166-1 alpha-2 |
| jobLocationType | remote_type | Only set "TELECOMMUTE" for remote jobs |
| baseSalary | salary_min/max/currency/period | Only include if salary data exists |
| directApply | - | `false` (we link to external apply URLs) |

### Employment Type Mapping
```php
match($job->employment_type) {
    'full_time' => 'FULL_TIME',
    'part_time' => 'PART_TIME',
    'contract' => 'CONTRACTOR',
    'freelance' => 'CONTRACTOR',
    'internship' => 'INTERN',
};
```

### Salary Period Mapping
```php
match($job->salary_period) {
    'year' => 'YEAR',
    'month' => 'MONTH',
    'hour' => 'HOUR',
};
```

### Validation Rules
- `title` is required
- `description` must be HTML
- `datePosted` is required
- `validThrough` should be set (Google penalizes without it). Default: posted_at + 30 days
- `hiringOrganization` is required
- Either `jobLocation` OR `jobLocationType: TELECOMMUTE` must be present
- Salary is recommended but not required
- Don't include salary if not available (no zeros or placeholders)

---

## 2. URL Structure

### Job Detail Pages
```
/jobs/{slug}
```
Slug format: `{sanitized-title}-{company}-{city}-{short-id}`
Example: `/jobs/senior-architect-foster-partners-london-a1b2c3`

### Category Pages
```
/jobs/category/{slug}
```
Example: `/jobs/category/architect`

### Location Pages
```
/jobs/location/{country}
/jobs/location/{country}/{city}
```
Example: `/jobs/location/gb/london`

### Search/Filter Pages
```
/jobs?q=revit&remote=true&category=architect
```
Note: Search result pages should use `noindex` meta if heavily filtered to avoid thin content.

---

## 3. Meta Tags

### Job Detail Page
```html
<title>Senior Architect at Foster + Partners - London | ArchGee</title>
<meta name="description" content="Senior Architect position at Foster + Partners in London. Hybrid working. £60,000-£80,000/year. Apply now on ArchGee.">
<link rel="canonical" href="https://archgee.com/jobs/senior-architect-foster-partners-london-a1b2c3">
<meta property="og:title" content="Senior Architect at Foster + Partners">
<meta property="og:description" content="Hybrid | London | £60K-£80K">
<meta property="og:type" content="article">
<meta property="og:url" content="https://archgee.com/jobs/senior-architect-foster-partners-london-a1b2c3">
```

### Category Page
```html
<title>Architect Jobs - Architecture Careers | ArchGee</title>
<meta name="description" content="Browse the latest architect jobs. Find architecture positions at top firms worldwide. Updated daily.">
```

### Home Page
```html
<title>ArchGee - Architecture & Design Jobs</title>
<meta name="description" content="Find architecture, interior design, landscape architecture, and urban design jobs. AI-powered job board for built-environment professionals.">
```

---

## 4. Sitemap

### Dynamic Sitemap Generation
Use `spatie/laravel-sitemap` (already installed).

Include:
- `/` (home) — priority 1.0, daily
- `/jobs` (listing) — priority 0.9, daily
- `/jobs/{slug}` (each approved job) — priority 0.8, weekly
- `/jobs/category/{slug}` (each category) — priority 0.7, weekly
- `/blog/{slug}` (blog posts) — priority 0.6, monthly

Exclude:
- Expired/rejected jobs
- Filtered search result URLs
- Admin/dashboard pages
- API endpoints

### Sitemap Index
For large job counts (>1000), split into multiple sitemaps:
```
/sitemap_index.xml
  → /sitemaps/jobs-1.xml
  → /sitemaps/jobs-2.xml
  → /sitemaps/categories.xml
  → /sitemaps/pages.xml
```

---

## 5. Robots.txt

```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /dashboard/
Disallow: /api/
Disallow: /checkout/
Disallow: /horizon/
Disallow: /telescope/

Sitemap: https://archgee.com/sitemap.xml
```

---

## 6. Performance & Core Web Vitals

- Lazy-load images below the fold
- Use `loading="lazy"` on company logos
- Minimize JavaScript bundle size
- Server-side render job listings (Livewire handles this)
- Cache job detail pages (1 hour TTL)
- Use CDN for static assets
- Compress images (WebP format for logos)

---

## 7. Internal Linking

- Each job detail page links to its category page
- Category pages link to related categories
- "Similar Jobs" section on job detail pages
- Breadcrumbs: Home > Jobs > Category > Job Title
- Blog posts link to relevant job categories

---

## 8. Implementation Checklist

- [ ] Job detail pages render JSON-LD structured data
- [ ] Proper `<title>` and `<meta description>` on all pages
- [ ] Canonical URLs on all pages
- [ ] Sitemap generated and registered with Google Search Console
- [ ] robots.txt configured
- [ ] Open Graph tags for social sharing
- [ ] Breadcrumb structured data
- [ ] Category and location pages are indexable
- [ ] Expired jobs return 410 Gone (not 404)
- [ ] Rich snippets validated via Google's Rich Results Test
