# ArchGee UI Verification Guidelines

> Comprehensive checklist and automation strategy for verifying ArchGee's frontend meets design, functional, accessibility, and responsive requirements.

---

## Table of Contents

1. [Design System Reference](#1-design-system-reference)
2. [Page-by-Page Checklist](#2-page-by-page-checklist)
3. [Component-Level Checks](#3-component-level-checks)
4. [Responsive Breakpoints](#4-responsive-breakpoints)
5. [Accessibility (a11y)](#5-accessibility-a11y)
6. [Micro-Interactions & Animations](#6-micro-interactions--animations)
7. [Integration Readiness](#7-integration-readiness)
8. [Automated Visual Verification Strategy](#8-automated-visual-verification-strategy)
9. [Pass / Fail Criteria](#9-pass--fail-criteria)

---

## 1. Design System Reference

### 1.1 Color Palette

| Token | Hex | Usage |
|---|---|---|
| `primary-500` | `#FF9228` | CTA buttons, links, accents, brand identity |
| `primary-400` | `#FFA038` | Hover text on dark backgrounds |
| `primary-600` | `#F07A10` | Button hover states |
| `primary-100` | `#FFEBD4` | Light accent backgrounds (featured badge on light bg) |
| `secondary-950` | `#1E222B` | Dark backgrounds (hero, header, footer) |
| `secondary-900` | `#343B47` | Dark text on light backgrounds |
| `secondary-500` | `#677791` | Muted text |
| `secondary-400` | `#8694AB` | Placeholder text, hint text |
| `emerald-50/700` | — | Remote work type badge |
| `blue-50/700` | — | Hybrid work type badge |
| `amber-50/700` | — | On-site work type badge |

### 1.2 Typography

| Element | Font | Weight | Size |
|---|---|---|---|
| Body | Poppins | 400 | `text-base` (1rem) |
| H1 (Hero) | Poppins | 700 | `text-4xl` → `text-7xl` (responsive) |
| H1 (Page) | Poppins | 700 | `text-3xl` → `text-4xl` |
| H2 Section | Poppins | 700 | `text-2xl` → `text-3xl` |
| H3 Card | Poppins | 600 | `text-lg` |
| Labels | Poppins | 600 | `text-sm` |
| Body text | Poppins | 400 | `text-base` |
| Small / muted | Poppins | 400-500 | `text-xs` / `text-sm` |

### 1.3 Spacing & Radius

| Element | Spacing | Radius |
|---|---|---|
| Page sections | `py-16` (`4rem`) | — |
| Card padding | `p-5` or `p-6` | `rounded-xl` (0.75rem) |
| Form card | `p-6 md:p-8` | `rounded-2xl` (1rem) |
| Buttons | `px-6 py-3` or `px-8 py-3.5` | `rounded-xl` |
| Input fields | `px-4 py-3` | `rounded-xl` |
| Badges/pills | `px-2 py-0.5` or `px-3 py-1.5` | `rounded-full` or `rounded-lg` |

### 1.4 Logo

| Variant | File | Usage |
|---|---|---|
| Full logo (rounded) | `/public/images/archgee-logo.png` | Hero, about sections |
| Square logo | `/public/images/archgee-logo-square.png` | OG images, metadata |
| Header logo (48px) | `/public/images/archgee-logo-48.png` | Navbar |
| Resized (200px) | `/public/images/archgee-logo-200.png` | Footer, marketing |

---

## 2. Page-by-Page Checklist

### 2.1 Landing Page (`/`)

#### Hero Section
- [ ] Dark gradient background (`arch-gradient` + `arch-lines`) renders correctly
- [ ] Ambient glow orbs visible with `blur-3xl` effect
- [ ] Logo image renders at correct size in header
- [ ] Pill badge "The #1 job board for architects" displays with star icon
- [ ] Headline "Design the world. Find your stage." renders in white + primary-400
- [ ] Subheading text is `secondary-300` and legible
- [ ] Search bar has glass-morphism effect (`bg-white/10 backdrop-blur-sm`)
- [ ] Search input accepts text and submits to `/jobs`
- [ ] "Search Jobs" button is `primary-500`, has `pulse-gentle` animation
- [ ] Quick filter pills (Remote, Full Time, Senior, Junior, Internship) link correctly
- [ ] Stats section shows Active Jobs count, Countries (15+), Specializations
- [ ] Bottom gradient fade (`from-gray-50`) transitions smoothly to next section

#### Categories Section
- [ ] Section title "Explore by Specialization" renders
- [ ] Category cards display in 2x2 (mobile) / 3-col (tablet) / 4-col (desktop) grid
- [ ] Each card shows category name and job count
- [ ] Hover: border changes to `primary-300`, shadow appears, arrow moves right
- [ ] Cards link to `/jobs?category={slug}`
- [ ] `fade-in-up` animation triggers on scroll

#### Latest Jobs Section
- [ ] Section heading "Latest Opportunities" with "View all jobs" link
- [ ] Job cards render as list with proper spacing (`space-y-3`)
- [ ] Featured jobs have left orange border (`job-tile-featured`)
- [ ] Featured badge shows star icon + "Featured" text
- [ ] Job title, company, location, remote type badge, category badge visible
- [ ] Salary displayed in `primary-600` when available
- [ ] Posted time shows relative format ("2 hours ago")
- [ ] Cards link to `/jobs/{slug}`
- [ ] "Browse All Jobs" button at bottom
- [ ] Empty state shows cube icon, "No jobs posted yet", "Post a Job" CTA

#### CTA Section
- [ ] Dark gradient background with glow orb
- [ ] "Ready to shape the future?" headline
- [ ] Two buttons: "Find Jobs" (primary solid) + "Post a Job" (ghost/outline)
- [ ] `fade-in-up` animation on scroll

### 2.2 Job Search Page (`/jobs`)

#### Header / Search
- [ ] Dark `secondary-950` header with `arch-lines`
- [ ] Page title "Architecture & Design Jobs"
- [ ] Search input pre-fills with current `q` query param
- [ ] Search button submits form
- [ ] 5 filter dropdowns: Category, Work Type, Seniority, Location text, Employment Type
- [ ] Filters auto-submit on `change` event (select elements)
- [ ] Selected filter values persist after page reload
- [ ] Filter dropdowns have dark option backgrounds matching header

#### Results
- [ ] Results count header: "{N} jobs found"
- [ ] "Clear Filters" link appears when any filter is active
- [ ] Job cards identical in design to homepage Latest Jobs cards
- [ ] Featured jobs show `job-tile-featured` left border
- [ ] All badges (remote type, category, seniority, employment type) render
- [ ] Cards link to individual job page
- [ ] Pagination renders below results (Laravel default)
- [ ] Pagination preserves query string parameters

#### Empty State
- [ ] Search icon illustration (magnifying glass)
- [ ] "No jobs found matching your criteria." message
- [ ] "Try adjusting your filters or search terms." hint
- [ ] "Clear All Filters" button links to `/jobs`

### 2.3 Job Detail Page (`/jobs/{slug}`)

#### Header Banner
- [ ] Dark `secondary-950` background
- [ ] Breadcrumbs: Home > Jobs > [Category] > [Job Title]
- [ ] Featured badge (if `is_featured`)
- [ ] Job title in `text-2xl md:text-3xl` white text
- [ ] Company name + website link (opens in new tab)
- [ ] Tag row: location, remote type (color-coded), category, seniority, employment type
- [ ] Salary in `primary-400` text
- [ ] "Apply Now" button with `pulse-gentle` animation
- [ ] Posted date + expiry date

#### Content Area
- [ ] Two-column layout: 2/3 main + 1/3 sidebar on desktop
- [ ] Single column on mobile
- [ ] Description card: `prose` formatting for HTML content
- [ ] Skills & Tools card: tag pills in `secondary-50` background
- [ ] Sidebar: Apply card with "Apply Now" or "Apply via Email" button
- [ ] Sidebar: Job Details card with icon list (location, type, posted, salary)

#### Similar Jobs
- [ ] "Similar Jobs" heading
- [ ] 2-column grid of job cards
- [ ] Cards show title, company, location, posted time
- [ ] Cards link to respective job detail pages
- [ ] Hidden when no similar jobs exist

#### SEO / Schema
- [ ] `<meta name="description">` tag with job description excerpt
- [ ] Canonical URL set
- [ ] Open Graph title, description, type, URL
- [ ] Google Jobs structured data (`application/ld+json`)

### 2.4 Job Posting Form (`/jobs/post`)

#### Header
- [ ] Dark header with breadcrumbs (Home > Post a Job)
- [ ] "Free to post" pill badge
- [ ] "Find your next great hire" headline
- [ ] Description text about review process
- [ ] SEO meta tags (description, canonical)

#### Form — Progressive Disclosure (3 Steps)
- [ ] Step indicator with numbered circles (1 = The Role, 2 = Details, 3 = How to Apply)
- [ ] Active step has `ring-4` glow effect
- [ ] Completed steps show checkmark icon
- [ ] Connector lines turn `primary-500` when step is completed
- [ ] Step labels hidden on mobile (`hidden sm:block`)

**Step 1: The Role**
- [ ] "Tell us about the role" heading
- [ ] Job Title input: required, placeholder text
- [ ] Job Description textarea: required, 8 rows, min 50 chars
- [ ] Helper text: "Minimum 50 characters. Tip: Include responsibilities..."
- [ ] "Continue" button (right-aligned)
- [ ] Validation errors render in red below fields

**Step 2: Details**
- [ ] "Company & job details" heading
- [ ] Company Name + Website inputs (2-col grid)
- [ ] Location input with map pin icon
- [ ] Work Type select + Employment Type select (2-col grid)
- [ ] "Back" button (left) + "Continue" button (right)

**Step 3: How to Apply**
- [ ] "How should candidates apply?" heading
- [ ] Application URL input with link icon
- [ ] "or" divider between URL and email
- [ ] Application Email input with mail icon
- [ ] Info callout: "Either an application URL or email is required"
- [ ] Submitter email input (optional) with user icon
- [ ] "Back" button + "Submit Job" button with airplane icon
- [ ] Submit button has `pulse-gentle` animation
- [ ] Loading state: spinner + "Submitting..." text
- [ ] Button disabled during submission (`wire:loading.attr="disabled"`)

**Reassurance Badges**
- [ ] Three badges below form: "Reviewed by our team", "Usually approved within 24h", "Global reach"
- [ ] Each has a colored icon (emerald shield, orange clock, blue globe)

**Success State**
- [ ] Large green checkmark in emerald circle
- [ ] "Job Submitted Successfully!" heading
- [ ] Description about review process
- [ ] "Browse Jobs" button (primary) + "Post Another" button (outline)
- [ ] `fade-in-up` animation on success

---

## 3. Component-Level Checks

### 3.1 Header / Navbar
- [ ] Logo image (48px) with "ArchGee" text renders correctly
- [ ] Dark `secondary-950` background with bottom border
- [ ] Nav links: "Find Jobs", "Post a Job", "Blog"
- [ ] Active nav link highlighted with `primary-400`
- [ ] "Login" link visible when not authenticated (hidden on mobile)
- [ ] User menu dropdown when authenticated
- [ ] "Post a Job" CTA button in `primary-500`
- [ ] Mobile hamburger menu toggles dropdown
- [ ] Mobile dropdown has dark background and proper z-index
- [ ] Announcement bar (if active) renders above nav

### 3.2 Footer
- [ ] Dark `secondary-950` background
- [ ] Logo image (200px) in brand section
- [ ] Brand description text
- [ ] 4-column grid: Brand, For Professionals, For Employers, Company
- [ ] All links are `secondary-400` → `primary-400` on hover
- [ ] Social media icons render (Twitter, LinkedIn, Instagram, GitHub)
- [ ] Copyright with current year
- [ ] Responsive: stacks to single column on mobile

### 3.3 Job Card / Job Tile
- [ ] White background, `rounded-xl`, `border-gray-100`
- [ ] Hover: border turns `primary-300/amber`, shadow appears, `translateY(-2px)`
- [ ] Featured: left orange border, subtle gradient bg
- [ ] Title: `text-base font-semibold text-secondary-900`
- [ ] Company: `text-sm text-secondary-500`
- [ ] Location icon + text
- [ ] Remote type badge: color-coded (emerald/blue/amber)
- [ ] Category badge: `secondary-100` bg
- [ ] Salary: `primary-600` right-aligned
- [ ] Posted time: `text-xs text-secondary-400`

### 3.4 Form Inputs (Custom Design)
- [ ] Rounded-xl border, `bg-gray-50/50`
- [ ] Focus: `border-primary-500`, `ring-2 ring-primary-500/20`
- [ ] Placeholder: `text-secondary-400`
- [ ] Value text: `text-secondary-900`
- [ ] Error state: `text-red-500` message below field
- [ ] Icon-prefixed inputs: icon `left-3.5`, input `pl-11`
- [ ] Select dropdowns: `appearance-none` with custom styling

### 3.5 Buttons

| Type | Normal | Hover | Active |
|---|---|---|---|
| Primary CTA | `bg-primary-500 text-white` | `bg-primary-600 shadow-lg shadow-primary-500/25` | — |
| Secondary | `bg-secondary-950 text-white` | `bg-secondary-800` | — |
| Ghost/Outline | `bg-white/10 text-white border-white/15` | `bg-white/15` | — |
| Text/Back | `text-secondary-600` | `text-secondary-900` | — |
| Disabled | `opacity-70 cursor-not-allowed` | No change | — |

---

## 4. Responsive Breakpoints

### 4.1 Breakpoint Targets

| Device | Width | Key Behavior |
|---|---|---|
| Mobile | 375px | Single column, stacked elements, burger menu |
| Tablet | 768px | 2-col grids, inline search, visible nav |
| Desktop | 1024px+ | Full layout, sidebar visible, 4-col grid |
| Large Desktop | 1440px | Centered content with max-width constraints |

### 4.2 Per-Page Responsive Checks

#### Landing Page
- [ ] **Mobile (375px)**: Hero text `text-4xl`, search stacks vertically, stats wrap, categories 2-col, jobs single column
- [ ] **Tablet (768px)**: Hero text `text-6xl`, search inline, categories 3-col, jobs have horizontal layout
- [ ] **Desktop (1024px+)**: Full hero `text-7xl`, categories 4-col, full layout

#### Job Search Page
- [ ] **Mobile**: Search stacks, filter dropdowns wrap, job cards full-width
- [ ] **Tablet**: Search inline, filters wrap in rows
- [ ] **Desktop**: Search inline, filters single row, full card layout

#### Job Detail Page
- [ ] **Mobile**: Single column, sidebar below content, apply button full-width
- [ ] **Tablet**: Single column but wider cards
- [ ] **Desktop**: 2/3 + 1/3 sidebar layout

#### Job Post Form
- [ ] **Mobile**: Step labels hidden, form fields single column, full-width buttons
- [ ] **Tablet**: Step labels visible, 2-col grids
- [ ] **Desktop**: Same as tablet, wider max-width

### 4.3 Navigation Responsiveness
- [ ] **Mobile (< 1024px)**: Hamburger menu visible, desktop nav hidden
- [ ] **Desktop (>= 1024px)**: Full nav visible, hamburger hidden
- [ ] **Mobile dropdown**: full-width with proper z-index (z-50)

---

## 5. Accessibility (a11y)

### 5.1 Color Contrast (WCAG AA)
- [ ] White text on `secondary-950` (#1E222B): ratio >= 4.5:1 ✓
- [ ] `secondary-300` (#B1BAC9) on `secondary-950`: check >= 4.5:1
- [ ] `primary-500` (#FF9228) on white: check >= 3:1 for large text
- [ ] `primary-600` (#F07A10) on white: check >= 4.5:1
- [ ] `secondary-500` (#677791) on white: check >= 4.5:1
- [ ] Red error text (`text-red-500`) on white/light backgrounds: >= 4.5:1
- [ ] Badge text colors against their backgrounds meet minimum ratios

### 5.2 Keyboard Navigation
- [ ] All interactive elements (buttons, links, inputs) focusable via Tab
- [ ] Focus visible: ring or outline appears on focus
- [ ] Form inputs have visible focus states (`ring-2 ring-primary-500/20`)
- [ ] Dropdown menus navigable via keyboard
- [ ] Step navigation in form works with keyboard
- [ ] Escape closes mobile menu

### 5.3 Screen Reader
- [ ] All images have `alt` text (logo, icons can be `aria-hidden`)
- [ ] SVG icons have `aria-hidden="true"` when decorative
- [ ] Form labels linked to inputs via `for`/`id` attributes
- [ ] Required fields marked with `aria-required` or visible asterisk
- [ ] Error messages associated with fields via `aria-describedby`
- [ ] Page structure uses semantic HTML (nav, main, section, footer, h1-h3)
- [ ] Breadcrumbs use `<nav>` with `aria-label="Breadcrumb"`

### 5.4 Forms
- [ ] All `<label>` elements have matching `for`/`id`
- [ ] Required fields have visible indicator (red asterisk)
- [ ] Error messages appear near the field
- [ ] Submit button disabled state is clear
- [ ] Loading state provides feedback (spinner + text change)

---

## 6. Micro-Interactions & Animations

### 6.1 Animation Inventory

| Animation | Class | Duration | Trigger |
|---|---|---|---|
| Fade in up | `fade-in-up` | 0.6s | Scroll into view (`x-intersect`) |
| Fade in | `fade-in` | 0.5s | Element appears |
| Pulse CTA | `pulse-gentle` | 3s infinite | Always (CTA buttons) |
| Hover lift | `hover-lift` | 0.3s | Mouse hover |
| Job tile hover | `job-tile` | 0.3s cubic-bezier | Mouse hover |
| Search glow | `search-glow` | — | Focus within |
| Step transition | `translate-x-4 → translate-x-0` | 0.3s | Step change |
| Stagger | `stagger-1` to `stagger-5` | delay 0.1-0.5s | Paired with animations |

### 6.2 Verification Checks
- [ ] `pulse-gentle` visible on "Search Jobs", "Apply Now", and "Submit Job" buttons
- [ ] `fade-in-up` triggers once when sections scroll into view
- [ ] Job card hover: border color change + translateY(-2px) + shadow
- [ ] Category card hover: border + shadow + arrow translate
- [ ] Search input focus: `ring-primary-500/50` glow
- [ ] Form step transitions: smooth slide from right
- [ ] Step indicator: circle scales up on active, checkmark on complete
- [ ] Button hover: `shadow-lg shadow-primary-500/25` glow
- [ ] Nav link hover: `text-primary-400` color transition
- [ ] Footer link hover: `primary-400` color transition

---

## 7. Integration Readiness

### 7.1 Buttons & Links
- [ ] "Search Jobs" (hero): submits to `GET /jobs?q={query}`
- [ ] Quick filter pills (hero): link to `/jobs?remote=remote`, etc.
- [ ] "Post a Job" (header CTA): links to `/jobs/post`
- [ ] "Apply Now": `POST /jobs/{slug}/apply` → redirects to external URL
- [ ] "Apply via Email": `mailto:{email}` link
- [ ] "Browse Jobs": links to `/jobs`
- [ ] Category cards: link to `/jobs?category={slug}`
- [ ] Job cards: link to `/jobs/{slug}`
- [ ] Breadcrumb links navigate correctly
- [ ] Footer links: all route correctly
- [ ] Pagination links: preserve query params

### 7.2 Forms
- [ ] Search form: GET `/jobs` with `q`, `category`, `remote`, `seniority`, `location`, `employment_type`
- [ ] Job posting form: Livewire `wire:submit="submit"`
- [ ] CSRF token present on POST forms (`@csrf`)
- [ ] Validation errors render from Livewire server-side validation
- [ ] `wire:model` bindings on all form fields
- [ ] `wire:loading` states on submit button

### 7.3 SEO
- [ ] All pages have `<title>` tags
- [ ] `<meta name="description">` on all pages
- [ ] Canonical URLs on job detail and post pages
- [ ] Open Graph tags on job detail pages
- [ ] Google Jobs JSON-LD on job detail pages
- [ ] `sitemapped` middleware on index routes

---

## 8. Automated Visual Verification Strategy

### 8.1 Screenshot Capture (Puppeteer / Playwright)

```javascript
// Example: screenshots.mjs (Node.js / Playwright)
import { chromium } from 'playwright';

const BASE_URL = 'http://localhost:8000';
const VIEWPORTS = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1440, height: 900 },
];

const PAGES = [
  { name: 'home', path: '/' },
  { name: 'jobs-index', path: '/jobs' },
  { name: 'jobs-post', path: '/jobs/post' },
  // Job detail requires seeded data:
  // { name: 'jobs-show', path: '/jobs/sample-job-slug' },
];

(async () => {
  const browser = await chromium.launch();

  for (const viewport of VIEWPORTS) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();

    for (const p of PAGES) {
      await page.goto(`${BASE_URL}${p.path}`, { waitUntil: 'networkidle' });
      await page.screenshot({
        path: `screenshots/${viewport.name}-${p.name}.png`,
        fullPage: true,
      });
      console.log(`✓ ${viewport.name} → ${p.name}`);
    }

    await context.close();
  }

  await browser.close();
})();
```

### 8.2 Visual Diff (pixelmatch)

```javascript
// Example: visual-diff.mjs
import fs from 'fs';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

function compareImages(baselinePath, currentPath, diffPath) {
  const baseline = PNG.sync.read(fs.readFileSync(baselinePath));
  const current = PNG.sync.read(fs.readFileSync(currentPath));
  const { width, height } = baseline;
  const diff = new PNG({ width, height });

  const numDiffPixels = pixelmatch(
    baseline.data, current.data, diff.data,
    width, height,
    { threshold: 0.1 }
  );

  fs.writeFileSync(diffPath, PNG.sync.write(diff));

  const totalPixels = width * height;
  const diffPercentage = (numDiffPixels / totalPixels * 100).toFixed(2);

  return { numDiffPixels, diffPercentage, pass: diffPercentage < 1.0 };
}

// Usage:
// compareImages('baseline/desktop-home.png', 'screenshots/desktop-home.png', 'diffs/desktop-home.png');
```

### 8.3 Functional Testing (Playwright)

```javascript
// Example: functional-tests.spec.js (Playwright Test)
import { test, expect } from '@playwright/test';

test.describe('Job Search', () => {
  test('search filters update results', async ({ page }) => {
    await page.goto('/jobs');
    await page.selectOption('select[name="remote"]', 'remote');
    await page.waitForURL(/remote=remote/);
    await expect(page.locator('text=jobs found')).toBeVisible();
  });

  test('job cards link to detail page', async ({ page }) => {
    await page.goto('/jobs');
    const firstCard = page.locator('.job-tile').first();
    const href = await firstCard.getAttribute('href');
    await firstCard.click();
    await expect(page).toHaveURL(href);
  });
});

test.describe('Job Post Form', () => {
  test('step navigation works', async ({ page }) => {
    await page.goto('/jobs/post');
    await expect(page.locator('text=Tell us about the role')).toBeVisible();
    await page.click('text=Continue');
    await expect(page.locator('text=Company & job details')).toBeVisible();
  });

  test('required fields show validation', async ({ page }) => {
    await page.goto('/jobs/post');
    // Navigate to step 3 and try to submit without filling
    await page.click('text=Continue');
    await page.click('text=Continue');
    await page.click('text=Submit Job');
    // Validation messages should appear (Livewire server-side)
  });
});
```

### 8.4 Tailwind Class Verification

```bash
# Check primary-500 usage across views
grep -rn "primary-500" resources/views/ --include="*.blade.php" | head -20

# Check all hover states
grep -rn "hover:" resources/views/ --include="*.blade.php" | grep -c "hover:bg-primary-600"

# Verify no stale purple/old brand colors
grep -rn "#6f27e5\|purple-\|violet-" resources/views/ --include="*.blade.php"

# Check all form labels have for/id pairs
grep -n "for=" resources/views/livewire/jobs/post-job-form.blade.php
grep -n "id=" resources/views/livewire/jobs/post-job-form.blade.php
```

---

## 9. Pass / Fail Criteria

### Visual (Must Pass)
- Primary brand color `#FF9228` used consistently across all CTA buttons, active states, and accent elements
- No leftover purple/violet or SaaSykit default colors
- Logo renders correctly at all sizes (48px header, 200px footer/hero)
- Typography uses Poppins font family throughout
- Dark sections use `secondary-950` background consistently
- Job cards follow the `job-tile` design pattern

### Functional (Must Pass)
- All navigation links resolve to correct routes
- Search form submits and filters persist in URL
- Filter dropdowns auto-submit on change
- Job posting form: all 3 steps navigable
- Job posting form: server-side validation works
- Job posting form: submit creates job and shows success
- Apply Now button tracks click and redirects
- Pagination works with query string preserved

### Responsive (Must Pass)
- No horizontal overflow on mobile (375px)
- Navigation collapses to hamburger on mobile
- All text readable without zooming on mobile
- Form fields stack single-column on mobile
- Sidebar stacks below main content on mobile
- Images scale properly (no overflow or cropping issues)

### Accessibility (Should Pass)
- Color contrast meets WCAG AA (4.5:1 normal text, 3:1 large text)
- All form inputs have associated labels
- Focus states visible on all interactive elements
- Page structure uses semantic HTML (nav, main, section, h1-h3, footer)

### Performance (Should Pass)
- Initial page load under 3 seconds on 3G
- No layout shift during page load (CLS < 0.1)
- CSS + JS bundle under 200KB gzipped (excluding fonts)
- Images optimized (logo < 50KB for web variants)

---

## Appendix: File Reference

| File | Purpose |
|---|---|
| `resources/views/home.blade.php` | Landing page |
| `resources/views/jobs/index.blade.php` | Job search/listing |
| `resources/views/jobs/show.blade.php` | Job detail |
| `resources/views/jobs/post.blade.php` | Post job wrapper |
| `resources/views/livewire/jobs/post-job-form.blade.php` | Livewire form (3-step) |
| `resources/views/components/layouts/app.blade.php` | Main layout |
| `resources/views/components/layouts/app/header.blade.php` | Navbar |
| `resources/views/components/layouts/app/footer.blade.php` | Footer |
| `resources/views/components/layouts/app/navigation-links.blade.php` | Nav items |
| `resources/css/colors.css` | Theme color variables |
| `resources/css/styles.css` | Custom utilities & animations |
| `app/Livewire/Jobs/PostJobForm.php` | Form backend |
| `app/Http/Controllers/JobsController.php` | Page controllers |
