# Continuous Engineering Review (REVIEW.md)

## Repository Cleanup Review (15 Oct 2026)

- Renamed the assignment and Figma-link files and moved the email brief, progress tracker, and review into `docs/`; updated repository references.
- Removed only the user-approved scratch request and log files; no environment files were opened, modified, or deleted.
- Added missing root ignore patterns for logs, pytest cache, E2E request scratch, and versioned Python virtual environments.
- Post-cleanup checks passed: backend pytest (7), Django system check, provider pytest (4), frontend lint, and frontend production build.

This document is maintained after every development phase to self-review implementation coverage, security, edge cases, responsiveness, and design fidelity.

## Current Core Review (15 Oct 2026)

This section supersedes the early audit notes below where they report blocked verification. The stale port-8000 service was isolated from the current source; an isolated Django instance on port 8002 completed the live checks.

### Changes and Verification
- Added candidate status chips, made candidate names open communication history, and wired soft-delete to a confirmation dialog. Failed deletion requests now surface an error snackbar.
- Fixed TypeScript path aliases and the `parseISO` import. Moved the standalone Atlas ping script to `backend/scripts/check_db_ping.py` because pytest was executing it during collection.
- Backend: `python -m pytest backend`: **7 passed**; `manage.py check`: **no issues**. Provider: `python -m pytest provider-service/test_main.py`: **4 passed**. Frontend: `npm run lint`: **passed**; `npm run build`: **passed**.

### Remaining Issues
- Atlas ping and the webhook compound-index migration succeeded. Live API check verified candidate list/search/pagination, create, duplicate 409, and soft delete. Signed status callbacks, bulk per-recipient behavior, failure mapping, retries, and health were exercised against Atlas and the standalone provider.
- No browser screenshots were taken at 360/768/1280 widths. No mobile design frames or token file were found, so responsive visual fit is code-reviewed only.
- Added `POST /api/v1/messages` for one candidate, compound webhook event uniqueness, terminal failed-state protection, manual retry attempt reset, provider counts/rate evaluation, and a dashboard health card that disables sending when down. Migration applied; CORS is restricted to configured frontend origins.
- The single-candidate drawer now calls `/api/v1/messages`; bulk recipients call `/api/v1/messages/bulk`. Single-send success uses a snackbar, while partial/failure bulk results remain visible per recipient.
- The candidate table now hides nonessential columns on narrow screens and shows the phone under the candidate name to fit 360px without table-level horizontal scrolling. This was code-reviewed but not browser-screenshot verified.
- Applied `webhooks.0002_event_compound_uniqueness` to Atlas successfully. The corrected Atlas ping reports `candidate_comm` reachable.
- A terminal guard now prevents a late `queued`/`sent` event from reopening a failed recipient. History displays candidate ID, phone, and email; candidate create CTA stays disabled until local validation passes; history fetch errors now produce the retry state.
- Removed predictable Django and provider signing-secret fallbacks. Both processes now require their configured environment values and do not print them.
- An initial smoke request hit an older process on port 8000 and returned 0/4. The isolated current-source run below supersedes that result. Four demo attempt records from the stale-process run remain in Atlas history.
- Follow-up isolated E2E on port 8002 exercised the current source: 2 accepted and 2 failed for the four seeded suffixes; 0503 reached `read` with three attempts, 0500 reached `failed/delivery_failed`, outage produced retryable `provider_down` after three attempts, and manual retry reused the same recipient record. Provider health was operational before outage, down during it, and reachable afterward (degraded failure rate from the demo failures).
- Provider now deduplicates accepted sends by idempotency key. Provider suite: **4 passed**, including assertion that a repeated accepted key returns the existing provider message and does not schedule another lifecycle.
- Provider deterministic tests include accepted idempotency-key dedupe. A transient Windows `EPERM` creating `.next/static/chunks` cleared on rerun.

---

## Phase P0 Self-Review

### 1. Requirement & Asset Coverage
- Analyzed all 26 UI assets in `/design`, identifying 6 explicit developer notes:
  1. Recipient chip overflow: max 2 lines, followed by `+ n` chip.
  2. Message composition textarea must be vertically resizable.
  3. Single candidate delete confirmation must include candidate's full name in copy.
  4. Multiple candidate delete confirmation must show plural copy and `DELETE {N} CANDIDATES` button.
  5. Communication history must be ordered newest to oldest (reverse chronological).
  6. Table candidate names must have underline on hover and open communication drawer on click.
- Restored original assignment bonus features A (Templates), B (Scheduled Messages), C (Multiple Providers), D (Provider Health), E (Auto-retry).
- Confirmed live status polling (every 3s while visible messages are non-terminal) as a core feature.

### 2. Security & Data Protection
- `backend/.env` containing `MONGODB_URI` is strictly excluded from version control and shell outputs.
- `.gitignore` verified to block `.env`, `.env.*`, and temporary artifacts.
- HMAC-SHA256 signature verification specified for provider webhook callbacks.

### 3. Open Issues / Risks Tracked
- Python 3.14: Must test `django-mongodb-backend` compatibility.
- Bulk results edge cases: Design has no dedicated screen for partial failure in bulk send; documented fallback in `DECISIONS.md`.

---

## Phase P1 Self-Review: Scaffolding, DB Ping & Health Verification

### 1. Verification Run & Results
- **Provider Microservice (`/provider-service`)**:
  - Standalone FastAPI service running on port 8001.
  - Implemented `/health`, `/admin/outage`, `/v1/messages` with deterministic phone suffix dispatch, and HMAC-SHA256 signature generator.
  - Verified: `GET http://127.0.0.1:8001/health` -> `200 OK {"status": "ok", "outage": False}`.
- **Django REST Backend (`/backend`)**:
  - Python 3.13 venv with `django-6.1.2`, `django-mongodb-backend-6.1.0`, `pymongo-4.18.3`, and `djangorestframework-3.18.3`.
  - Resolved `HOST` configuration for `django-mongodb-backend` and configured `DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"`.
  - Startup database ping verified against real MongoDB Atlas cluster without exposing connection credentials.
  - Standardized JSON error handler implemented: `{"error": {"code": "...", "message": "...", "fields": {...}}}`.
  - Verified: `GET http://127.0.0.1:8000/api/v1/health` -> `200 OK {"status": "ok", "database": "ok"}`.
  - Verified: `GET http://127.0.0.1:8000/api/v1/health/provider` -> `200 OK {"status": "operational"}`.
- **Next.js Frontend (`/frontend`)**:
  - Next.js 14.2.25 App Router with TypeScript strict mode and Material UI (MUI v5).
  - Theme initialized from design tokens (Inter font, `#1976D2` primary, `#EBF3FE` highlight, `#EDF7ED` toast, touch targets >= 44px).
  - Production build compiled successfully (`npm run build`).
  - Verified: `GET http://127.0.0.1:3000` -> `200 OK` with live health check indicator.

### 2. Edge Cases & Obstacles Handled
- **Stale Port 8000 Bind**: Detected an orphan Python process holding port 8000; safely terminated the process to allow Django backend to bind cleanly.
- **DRF Auth Isolation**: Configured DRF settings with `UNAUTHENTICATED_USER = None` and empty auth classes to prevent unwanted imports of Django `ContentType` and default auth tables into MongoDB.

### 3. Current System State
- All 3 services are active, communicating, and verified healthy.
- Ready for Phase P2: Candidates backend models, validations, seed data, and frontend candidate table.
