# ArchGee Mobile App — Technical Guidelines

> This document describes the Kotlin Multiplatform mobile app that consumes the ArchGee Laravel REST API. The web PRD (`prd.md`) and API contract (`api_endpoints.md`) are the canonical sources for product scope, data models, and endpoint contracts. This file covers mobile-specific architecture, conventions, and integration details.

## Overview

- **Name**: ArchGee Mobile App
- **Type**: Kotlin Multiplatform (KMP) with Jetpack Compose Multiplatform
- **Platforms**: Android (minSdk 24, targetSdk 36) + iOS (via Xcode wrapper)
- **Location**: `ArchGee-MobileApp/` (separate git repo within the monorepo)
- **Package**: `com.measify.archgee`
- **Current Version**: 1.0.5 (versionCode 7)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Kotlin 2.1.x |
| **UI Framework** | Compose Multiplatform 1.8.x + Material3 |
| **Networking** | Ktor 3.x (OkHttp on Android, Darwin on iOS) |
| **Serialization** | Kotlinx Serialization 1.8.x |
| **DI** | Koin 4.x (core + compose + viewmodel) |
| **Database** | Room 2.7.x (BundledSQLiteDriver, cross-platform) |
| **Preferences** | Multiplatform Settings 1.1.x |
| **Auth** | Firebase Auth (gitlive-firebase) + KMPAuth (Google Sign-In) |
| **Monetization** | RevenueCat 2.x (in-app purchases/subscriptions) |
| **Push Notifications** | KMPNotifier 1.5.x |
| **Image Loading** | Coil 3.x (Ktor integration) |
| **Analytics** | Firebase Analytics, PostHog (optional) |
| **Ads** | Google AdMob (toggleable via feature flags) |
| **Crash Reporting** | Firebase Crashlytics |
| **Logging** | Napier + custom Telegram logger |
| **Navigation** | Jetpack Navigation Compose (type-safe `@Serializable` routes) |
| **Build** | Gradle Kotlin DSL, KSP, BuildConfig plugin |

## Module Structure

```
ArchGee-MobileApp/
├── composeApp/                    # Main application module
│   ├── src/commonMain/            # Shared Kotlin/Compose code
│   ├── src/androidMain/           # Android-specific (engine, Firebase, ads)
│   ├── src/iosMain/               # iOS-specific (engine, platform glue)
│   └── src/commonTest/            # Shared tests
├── designsystem/                  # Reusable UI component library
│   ├── src/commonMain/            # Shared components (40+ composables)
│   ├── src/androidMain/           # Android-specific components
│   ├── src/iosMain/               # iOS-specific components
│   └── src/jvmMain/               # Desktop preview (component gallery)
├── iosApp/                        # Xcode project wrapping shared code
├── distribution/                  # Release assets (keystore, release notes)
├── gradle/
│   ├── libs.versions.toml         # Version catalog
│   └── scripts/                   # Build helper scripts
└── .github/workflows/             # CI/CD (build, Play Store, App Store)
```

## Architecture

### Layered Architecture (Clean Architecture)

```
┌──────────────────────────────────────┐
│  Presentation Layer                  │
│  screens/ (MVVM: ScreenRoute +       │
│  UiStateHolder + UiState + UiEvent)  │
│  components/                         │
├──────────────────────────────────────┤
│  Domain Layer                        │
│  model/ (Job, User, Subscription,    │
│  JobFilters, Company, AuthProvider)  │
│  swipe/ (DailySwipeLimiter)         │
│  exceptions/                         │
├──────────────────────────────────────┤
│  Data Layer                          │
│  repository/ (JobRepository,         │
│  UserRepository, SubscriptionRepo)   │
│  source/remote/ (Ktor, API services) │
│  source/local/ (Room DB, DAOs)       │
│  source/preferences/                 │
│  BackgroundExecutor                  │
└──────────────────────────────────────┘
```

### MVVM Pattern Per Screen

Each screen follows this pattern:

```
ScreenRoute (@Serializable, implements ScreenRoute interface)
  └── Screen (@Composable, receives UiState + onEvent lambda)
      └── UiStateHolder (extends UiStateHolder/ViewModel)
          ├── StateFlow<UiState>  (reactive UI state)
          ├── onUiEvent(UiEvent)  (event handler)
          └── Repositories        (data access)
```

- **UiState**: Immutable data class holding all UI-relevant state
- **UiEvent**: Sealed class representing user interactions
- **UiStateHolder**: Base class extending AndroidX ViewModel; uses `uiStateHolderScope`
- **State composition**: Use `combine()` on multiple flows → `stateIn(WhileSubscribed(5000))`

### Key Screens

| Screen | Purpose |
|--------|---------|
| **Onboarding** | 3-4 swipeable intro panels (first launch only) |
| **Sign In** | Firebase Auth (anonymous auto-login, Google OAuth upgrade) |
| **Home** | Swipeable job cards with filtering, pagination, swipe limits |
| **Job Details** | Full description, external apply link tracking |
| **Saved Jobs** | Bookmarked jobs list |
| **Paywall** | RevenueCat subscription UI (free → premium upgrade) |
| **Profile** | User preferences, account settings |
| **Help & Support** | FAQ, contact |

### Navigation

- **Framework**: Jetpack Navigation Compose with `@Serializable` route classes
- **Pattern**: `ScreenRoute` interface with `@Composable Content()` method
- **Transitions**: Fade in/out (400ms)
- **Bottom Nav Tabs**: Home, Saved Jobs, Notifications, Profile
- **Flow**: Onboarding → Main (with bottom nav) → Paywall (modal)

## API Integration (Laravel Backend)

The mobile app consumes the ArchGee Laravel REST API. See `api_endpoints.md` for the full contract.

### Key Endpoints for Mobile

| Endpoint | Mobile Usage |
|----------|-------------|
| `GET /api/v1/jobs` | Home feed, search, filtered browsing |
| `GET /api/v1/jobs/{slug}` | Job detail screen |
| `GET /api/v1/categories` | Filter options |
| `POST /api/v1/saved-jobs` | Save/bookmark a job |
| `DELETE /api/v1/saved-jobs/{job_id}` | Unsave a job |
| `GET /api/v1/saved-jobs` | Saved jobs list |

### Request/Response Mapping

- **Request DTOs**: `data/source/remote/request/` — `GetJobsRequest`, `JobFiltersRequest`, etc.
- **Response DTOs**: `data/source/remote/response/` — `JobResponse`, `BaseApiResponse`, etc.
- All DTOs use `@Serializable` + `@SerialName` annotations
- Class names MUST have `Request`/`Response` suffix
- Each response DTO has an `asDomain()` method converting to domain models
- API services return raw data types (NOT `Result`); repositories wrap in `Result`

### HTTP Client (Ktor)

- **Factory**: `HttpClientFactory.kt`
- **Engines**: OkHttp (Android), Darwin (iOS) — via `expect/actual`
- **Timeouts**: 60s request, 10s connection, 60s socket
- **Auth**: Firebase ID token auto-attached to all requests
- **Content negotiation**: Kotlinx Serialization JSON (`ignoreUnknownKeys=true`)
- **Logging**: All requests logged via Napier

### API Service Pattern

```kotlin
// Interface (in data/source/remote/apiservices/)
interface JobApiService {
    suspend fun getJobs(request: GetJobsRequest): GetJobsResponse
    suspend fun saveJob(request: SaveJobRequest): SaveJobResponse
}

// Implementations:
// - FakeJobApiService (mock data for development)
// - RealJobApiService (production Ktor calls)
```

### Migration Notes (Current → Laravel API)

The mobile app currently uses `FakeJobApiService` with mock data. To integrate with the Laravel backend:

1. **Base URL**: Configure `ARCHGEE_API_URL` (e.g., `https://archgee.com/api/v1/`)
2. **Auth**: Replace Firebase ID token with Laravel Sanctum token (or implement Sanctum token exchange)
3. **Implement `RealJobApiService`**: Map to Laravel endpoints per `api_endpoints.md`
4. **Pagination**: Laravel uses `page` + `per_page` params, returns `meta` object with `current_page`, `last_page`, `total`
5. **Filters**: Map `JobFilters` → query params: `q`, `category`, `location`, `country`, `remote`, `seniority`, `employment_type`, `salary_min`, `salary_max`
6. **Job detail**: Use slug-based lookup (`/api/v1/jobs/{slug}`)
7. **Saved jobs**: `POST /api/v1/saved-jobs` (save) + `DELETE /api/v1/saved-jobs/{job_id}` (unsave) — requires Sanctum auth
8. **Apply tracking**: `POST /jobs/{slug}/apply` (web route, may need API equivalent)

## Data Persistence (Local)

### Room Database

- **File**: `data/source/local/AppDatabase.kt`
- **Version**: 3 (destructive migration fallback)
- **Driver**: BundledSQLiteDriver (cross-platform)
- **Entities**: `JobEntity`, `ExampleEntity`
- **DAOs**: `JobDao` (Flow-based queries for seen/unseen jobs, upsert, saved status)

### User Preferences

- **Multiplatform Settings** (SharedPreferences on Android, UserDefaults on iOS)
- Stores: daily swipe count, last swipe timestamp, first-time user flag, feature flags

## Business Logic

### Daily Swipe Limiter

- **Free users**: 4 swipes per day (configurable)
- **Premium users**: Unlimited
- **Reset**: 24-hour rolling window
- **Location**: `domain/swipe/DailySwipeLimiter.kt`
- **Triggers paywall** when limit reached

### Monetization

- **RevenueCat** handles all subscription management
- **Tiers**: Free (limited swipes, basic filters) → Premium (unlimited swipes, advanced filters, priority notifications)
- **Subscription state**: `SubscriptionRepository.currentSubscriptionFlow` (reactive)
- **Packages**: Fetched via RevenueCat for dynamic pricing

### Authentication Flow

1. First launch → anonymous Firebase sign-in
2. User can upgrade to Google OAuth
3. Auth state tracked via `UserRepository.currentUser: SharedFlow<Result<User>>`
4. **TODO**: Integrate Sanctum token exchange for Laravel API auth

## Design System

### Module: `designsystem/`

40+ reusable Compose components including:
- **JobCard**: Company logo, title, location, salary, remote badge
- **Buttons**: Primary (orange), secondary (dark), ghost variants
- **Navigation**: BottomNav, AppToolbar
- **Pagers**: AnimatedHorizontalPager (onboarding)
- **Modals**: MenuBottomSheet, ConfettiParticles
- **Auth**: AuthButtons (Google/Apple)
- **Feedback**: LoadingProgress, EmptyContentView

### Theme Alignment with Web

| Property | Web | Mobile |
|----------|-----|--------|
| **Primary color** | `#FF9228` | Should match — orange accent |
| **Secondary** | `#1E222B` | Dark backgrounds/text |
| **Font** | Poppins 400-700 | Poppins 400-700 |
| **Radius** | `rounded-xl` (0.75rem) | Equivalent dp values |
| **Remote badge** | Emerald | Emerald |
| **Hybrid badge** | Blue | Blue |
| **Onsite badge** | Amber | Amber |

## Feature Flags

Managed via Firebase Remote Config:
- `IS_ANALYTICS_ENABLED`: PostHog tracking toggle
- `IS_ADS_ENABLED`: AdMob ads toggle

## Build & Run Commands

```bash
# Android debug build
./gradlew :composeApp:assembleDebug

# Run shared unit tests
./gradlew :composeApp:testDebugUnitTest

# Android UI tests (device required)
./gradlew :composeApp:connectedDebugAndroidTest

# Firebase SHA1 for signing
./gradlew :composeApp:signingReport

# Design system desktop preview
# Run designsystem/src/jvmMain/kotlin/Main.kt from IDE
```

**iOS**: Build via Xcode only — do NOT run iOS builds during routine validation (they are slow).

## CI/CD

- `.github/workflows/build.yml` — PR/push builds
- `.github/workflows/publish_android_playstore.yml` — Play Store release
- `.github/workflows/publish_ios_appstore.yml` — App Store release

## Coding Conventions

### General
- Kotlin idiomatic style, Compose best practices
- Keep shared code in `commonMain`; platform code in `androidMain`/`iosMain`
- PSR-style: camelCase methods/variables, PascalCase classes
- Prefer suspend functions over callbacks
- Sealed classes for ADTs (events, results, errors)
- Early returns (happy path last)

### Domain Layer
- Pure, immutable `data class` models — no serialization annotations
- No platform-specific types in domain
- Exceptions: `UnAuthorizedException`, `PurchaseRequiredException`
- Call repositories directly from presentation (no pass-through use cases)
- Introduce use cases only for orchestration, business rules, or multi-repo coordination

### Data Layer
- **Concrete repositories** (no interfaces unless multiple implementations needed)
- **BackgroundExecutor** for IO operations
- **Result wrapping** at repository level only (not in API services)
- API services return raw types, let exceptions propagate
- Response DTOs include `asDomain()` mapping methods

### Coroutines
- Inject dispatchers for testability
- Use `SupervisorJob()` for independent child coroutines
- `ApplicationScope` for jobs outliving screens
- Avoid `GlobalScope`
- Use `TestDispatcher` in unit tests

### Testing
- Shared tests in `commonTest/`
- UI/Compose tests in `commonTest/screentest/`
- Provide fakes for API services (e.g., `FakeJobApiService`)
- Use `MockEngine` for Ktor in contract tests
- No real network calls in unit tests

## Domain Model Alignment (Mobile ↔ Laravel)

| Mobile Domain | Laravel Model | Notes |
|---------------|--------------|-------|
| `Job` | `Job` (UUID PK) | Map slug for detail lookups, id for save/unsave |
| `User` | User (Sanctum) | Firebase auth → Sanctum token exchange needed |
| `Subscription` | RevenueCat-managed | Server-side validation optional (Phase 2+) |
| `JobFilters` | Query params | Map to `q`, `category`, `location`, `country`, `remote`, etc. |
| `Company` | Part of Job | `company_name`, `company_logo_url` fields |

## Enums Alignment

| Mobile | Laravel Enum | Values |
|--------|-------------|--------|
| Work type | `RemoteType` | REMOTE, HYBRID, ONSITE |
| Seniority | `SeniorityLevel` | INTERN, JUNIOR, MID, SENIOR, LEAD, PRINCIPAL, DIRECTOR |
| Employment | `EmploymentType` | FULL_TIME, PART_TIME, CONTRACT, FREELANCE, INTERNSHIP |
| Job status | `JobStatus` | Mobile only sees APPROVED (published) jobs |

## Key Integration TODOs

1. Implement `RealJobApiService` against Laravel `/api/v1/` endpoints
2. Auth bridge: Firebase Auth → Laravel Sanctum token exchange
3. Sync saved jobs between local Room DB and server
4. Implement job alert endpoints when Phase 2 lands
5. Apply tracking: call server endpoint when user taps external apply link
6. Category data: fetch from `/api/v1/categories` for filter dropdowns
7. Align pagination: mobile currently uses page-based, matches Laravel's format
