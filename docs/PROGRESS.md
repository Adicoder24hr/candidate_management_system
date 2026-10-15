# Project Progress Tracker (PROGRESS.md)

**Project**: Candidate Communication & Management System  
**Last Updated**: October 2026  
**Current Phase**: Core P1–P5 verified; optional P6 bonuses and P7/P8 remain open  
**Status**: Executing Phases Continuously per Spec  

## 0. Current Audit (15 Oct 2026)

- Source files are located at `docs/ASSIGNMENT.md` and `docs/EMAIL_BRIEF.md`.
- Design inventory: dashboard/list → `design/candidate_communication_dashboard.png`, `design/candidate_communication.png`; empty list → `design/candidate_communication_empty_state.png`; create candidate → `design/add_candidate_dialog.png`, `design/add_candidate_dialog_with_name_filled.png`; selection → `design/candidate_selected_state.png`, `design/selecting_multiple_candidates.png`; delete → `design/candidate_delete_dialog_box.png`, `design/multiple_candidates_delete.png`; single send → `design/send_message_to_one_candidate_side_sliding_form.png`, `design/one_candidate_message_entered_state.png`; bulk send → `design/sending_message_to_multiple_candidates_form.png`, `design/message_sent_to_multiple_candidates.png`; history → `design/communication_history_side_form.png`, `design/communication_history_state.png`, `design/no_communication_history_state.png`.
- No mobile design frames or `design/TOKENS.md` are present. Responsive behavior remains an implementation assumption and has not been screenshot-verified.
- P1 Atlas ping, startup DB check, provider health, settings check, and frontend build were reproduced. Pytest collection was fixed by moving the operational ping script out of pytest discovery.
- P2 candidate create, duplicate rejection (409), soft delete (200), server-side search/pagination, and seeded candidate listing were exercised against the current Django source. UI build/lint pass; interactive browser behavior remains unverified.
- P3–P5 current-source API work: standalone single-send route (now used by the single-recipient UI), webhook pair uniqueness, terminal failed-state guard, auto/manual retry, friendly errors, provider counts/health, and down-state send disablement. Migration `webhooks.0002` is applied to Atlas.
- P2/P4 UI includes mobile table column collapse, candidate phone/email/ID in history, valid-form button gating, and history request error state. These changes pass lint/build but were not screenshot-verified.
- An initial request hit a stale Django process on port 8000 and returned 0/4; that run is superseded by the isolated current-source E2E below. Four demo attempt records may remain in Atlas audit history.
- Isolated current-source API E2E on port 8002: bulk seeded scenario returned 2 accepted, 2 failed; `0000` mapped invalid recipient, `0429` rate-limited, `0503` succeeded on attempt 3 and reached read, `0500` webhook reached failed/delivery_failed. Outage test returned down/provider_down after 3 attempts, and manual retry reused the same recipient ID. Provider restored to operational afterward.
- Verified on 15 Oct: backend tests (7 passed), provider tests (4 passed), backend `manage.py check` (no issues), frontend lint (clean), frontend production build (pass), Atlas ping (pass), webhook compound-index migration applied, and seeded API/provider/webhook/retry scenarios passed on the isolated current source. Browser checks at 360/768/1280 and visual comparison remain open.

---

## 1. Feature Checklist

### Core Requirements
- [ ] **1. Candidate Management & Table View**
  - [ ] Data table showing Full name, Mobile number, Last message date, Status, and Candidate ID
  - [ ] Column sorting with indicators
  - [ ] Search filter input with debounced query matching (server-side)
  - [ ] Pagination controls (`Rows per page: 10`, page navigation `|< < > >|`)
  - [ ] Status chips: `read` (green checkmark), `delivered` (teal checkmark), `Sent` (blue), `Failed` (red alert), `NA` (plain text)
  - [ ] Blue full name links with underline on hover (triggers communication history drawer)
  - [ ] Empty state illustration and prompt when no candidates exist
  - [ ] Soft deletion (`is_deleted: true`) to preserve communication audit trail
- [ ] **2. Add Candidate Flow & Validation**
  - [ ] "+ ADD CANDIDATE" modal dialog
  - [ ] Inputs: Full Name (2-80 chars), Mobile Number (E.164 normalized), Email Address (valid RFC)
  - [ ] Server-side validation rejecting duplicate phone/email with 409 conflict & clear field-level message (applied only to active records)
  - [ ] Disabled CTA until all required fields are valid
  - [ ] Success toast notification ("{Name} added successfully")
- [ ] **3. Candidate Selection & Batch Actions**
  - [ ] Single candidate row selection (row highlighted in `#EBF3FE`)
  - [ ] Multi-candidate selection with header checkbox ("select all on page")
  - [ ] Dynamic action buttons: "DELETE CANDIDATE" and "SEND MESSAGE" enabled when ≥ 1 selected
- [ ] **4. Send Message Drawer & Single Send**
  - [ ] Right-sliding drawer (`width: 480px` on desktop, 100vw on mobile)
  - [ ] Single candidate mode: pre-filled recipient chip
  - [ ] Resizable message textarea (`resize: vertical`)
  - [ ] Character counter & validation (disabled Send button if empty)
  - [ ] Dispatch to backend provider service
  - [ ] Success toast notification ("Message sent to 1 candidate")
- [ ] **5. Bulk Send & Independent Processing**
  - [ ] Multiple candidate mode: recipient chips with individual remove ('X') buttons
  - [ ] Chip overflow handling: maximum 2 lines of chips, remainder collapsed into `+ {n}` suffix chip
  - [ ] Each recipient processed independently as its own Message record (one failure never blocks others)
  - [ ] After submit: if all succeed, show Figma toast ("Message sent to N candidates"); if any fail, show per-candidate result view ("X succeeded, Y failed") with friendly failure reasons
- [ ] **6. Status Progression & Polling Updates**
  - [ ] Status ranks: `queued` (1) < `sent` (2) < `delivered` (3) < `read` (4)
  - [ ] `failed` accepted only if current status is `queued` or `sent`
  - [ ] Webhook endpoint `POST /api/v1/webhooks/provider/` with HMAC-SHA256 signature verification (`X-Provider-Signature`)
  - [ ] Idempotent webhook processing (unique `provider_message_id`, `event_id`)
  - [ ] Frontend polls every 3s while any visible message is non-terminal (stops once all are `read` or `failed`)
- [ ] **7. Failure Handling & Friendly Error Mapping**
  - [ ] Map provider errors to friendly human messages:
    - `invalid_recipient` -> "This phone number isn't valid or can't receive messages."
    - `rate_limited` -> "Too many messages sent. We'll retry shortly."
    - `temporary_failure` -> "The messaging service had a temporary problem."
    - `provider_down` -> "The messaging service is currently unavailable."
    - `delivery_failed` -> "The message couldn't be delivered to the recipient."
    - `unknown` -> "Something went wrong. Please try again."
  - [ ] Persist `error_code`, `friendly_message`, `retryable` (bool), `attempt_count`, `idempotency_key`, `channel` on MessageRecipient
  - [ ] Never display raw stack traces or raw provider codes to user
- [ ] **8. Communication History Per Candidate**
  - [ ] Triggered by clicking candidate full name in table
  - [ ] Candidate metadata header: Candidate ID, Full Name, Mobile number, Email address
  - [ ] Reverse-chronological message timeline (newest to oldest)
  - [ ] Message timestamp formatting: `DD-MM-YYYY | H:MM AM/PM` (IST)
  - [ ] Status chip per message: `read`, `delivered`, `Sent`, `Failed`
  - [ ] Display friendly failure reason if failed
  - [ ] "Retry" button visible only when retryable; permanent failure shows "Can't be retried: <reason>"
  - [ ] Empty history state with custom empty illustration and helpful copy
- [ ] **9. UX States Across All Screens**
  - [ ] Loading skeletons for tables and drawers
  - [ ] Empty candidate list illustration and prompt
  - [ ] Empty history state illustration and prompt
  - [ ] Failed request handling (inline error + Retry button)
  - [ ] Sending states (button disabled + spinner, double-submit prevention)
  - [ ] Form and field level validation feedback
  - [ ] Bottom-right snackbars matching Figma design system (`#EDF7ED` background, `#1E4620` text, green check icon)

---

### Bonus Features (Implemented in Order After Core)
- [ ] **E. Retry Failed Messages**
  - [ ] Classify retryable: `rate_limited`, `temporary_failure`, `provider_down`, `timeout`
  - [ ] Classify permanent: `invalid_recipient`, `delivery_failed`
  - [ ] Auto-retry retryable errors up to 3 times with exponential backoff: `min(2s * 2^attempt, 30s) + random jitter 0-500ms`
  - [ ] Manual "Retry" button reuses the same Message record with idempotency key
- [ ] **D. Provider Health Dashboard**
  - [ ] Provider health card: Status (`Operational` / `Degraded` / `Down`), counts for sent, delivered, failed, and success rate (`delivered / sent * 100`)
  - [ ] Health evaluation rules: Operational (<20% failure over last 20), Degraded (20-50%), Down (>50% or health check fails)
  - [ ] Warning banner and send button disablement / queued state when provider is Down
- [ ] **A. Message Templates with Placeholders**
  - [ ] Placeholders: `{{name}}`, `{{email}}`, `{{phone}}` rendered per candidate at send time
  - [ ] Live preview in UI
  - [ ] Validation rejecting unknown placeholders
- [ ] **B. Scheduled Messages**
  - [ ] Datetime picker (future only, IST)
  - [ ] Status "scheduled"
  - [ ] Background worker/command loop to send due messages; cancellation allowed while scheduled
- [ ] **C. Multiple Providers (Adapter Pattern)**
  - [ ] Define `ProviderAdapter` backend interface
  - [ ] Implement `dummy-whatsapp` and `dummy-email`
  - [ ] Channel selector in UI

---

## 2. Architecture & Microservices Checklist

- [x] **Ground Truth & Specs Analyzed** (`AGENTS.md`, `docs/ASSIGNMENT.md`, `docs/EMAIL_BRIEF.md`, all 26 Figma PNGs)
- [x] **Design Tokens & System Decisions Formulated** (`DECISIONS.md`)
- [ ] **Dummy Provider Microservice** (`/provider-service`)
  - [ ] Standalone service on port 8001 (FastAPI / ASGI)
  - [ ] `POST /v1/messages` (returns `provider_message_id`)
  - [ ] `GET /v1/messages/{id}`
  - [ ] `GET /health`
  - [ ] `POST /admin/outage {"on": true|false}`
  - [ ] Deterministic phone suffix rules:
    - ends `0000`: 422 `invalid_recipient`
    - ends `0429`: 429 `rate_limited` (with `Retry-After: 5`)
    - ends `0503`: 503 `temporary_failure` (passes on 3rd attempt)
    - ends `0500`: 202 accepted -> async webhook `delivery_failed`
    - other: 202 accepted -> async webhooks: `sent` (~1s), `delivered` (~3s), `read` (~6s)
  - [ ] Webhook simulation with HMAC-SHA256 signatures, 20% duplicate events, and occasional out-of-order delivery
- [ ] **Django REST Backend** (`/backend`)
  - [ ] Django 5.x + DRF project structure
  - [ ] Clean layering: views -> services -> provider adapters -> models
  - [ ] MongoDB Atlas connection to `candidate_comm` with fail-fast startup ping
  - [ ] Models: `Candidate`, `Message`, `MessageRecipient`, `WebhookEvent`
  - [ ] Versioned REST API endpoints under `/api/v1/`
  - [ ] Webhook verification & idempotent progression logic
  - [ ] Seed script with 11+ candidates (7 Figma + 4 deterministic failure tests + overflow)
- [ ] **Next.js Frontend** (`/frontend`)
  - [ ] Next.js (App Router) + React + TypeScript (strict) + Material UI
  - [ ] Design token theme (palette, typography, border-radius, spacing 8px)
  - [ ] Mobile-first responsive layout (360px up to 1440px+)
  - [ ] Reusable components: `StatusChip`, `EmptyState`, `ErrorState`, `ConfirmDialog`
  - [ ] Feature folders and typed API client

---

## 3. Verification Log

| Date | Phase / Milestone | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| Oct 2026 | P0 Ground Truth | Catalog 26 Figma PNGs, dev notes, and architecture | 26/26 assets cataloged; DECISIONS.md & docs/PROGRESS.md created | PASS |
| Oct 2026 | Env Var Security | Secure MONGODB_URI in backend/.env without logging | MONGODB_URI present; missing variables appended safely | PASS |
| Oct 2026 | P1 Provider Health | Standalone service on port 8001 responds 200 OK | GET /health returns 200 OK | PASS |
| Oct 2026 | P1 Backend & Atlas | Django 6 + django-mongodb-backend connects to Atlas | GET /api/v1/health returns 200 OK (DB: ok) | PASS |
| Oct 2026 | P1 Provider Proxy | Backend proxies provider health check | GET /api/v1/health/provider returns 200 OK | PASS |
| Oct 2026 | P1 Frontend MUI | Next.js 14 + MUI theme builds & renders | npm run build passes; GET / returns 200 OK | PASS |
| 15 Oct 2026 | P2 Candidate API E2E | Create, duplicate 409, soft delete, server-side search/pagination | All passed against isolated current-source API on Atlas | PASS |
| 15 Oct 2026 | P3–P5 Message E2E | Seed suffix outcomes, signed webhooks, retry and provider health | 0000 invalid; 0429 rate-limited; 0503 read after 3 attempts; 0500 delivery_failed; outage/provider_down and manual retry passed | PASS |
| 15 Oct 2026 | Automated checks | Backend/provider tests, Django checks, frontend lint/build | Backend 7 passed; provider 4 passed; Django check clean; lint/build passed | PASS |
| 15 Oct 2026 | P7 Visual review | Compare 360/768/1280 screenshots to design | Not run; screenshots/mobile frames unavailable | TODO |

---

## 4. Execution Phases

- [x] **P0: Read repository sources, catalog screens, author docs/PROGRESS.md & DECISIONS.md** (Complete; filenames corrected)
- [x] **P1: Scaffold 3 services, MUI theme from tokens, Mongo connection + ping, health endpoints** (Atlas ping, provider/backend health, frontend build reproduced)
- [x] **P2: Candidates (backend + UI) with validations, soft delete, and all UX states** (API create, duplicate 409, soft delete, search/pagination; UI lint/build. Browser interaction check remains open)
- [x] **P3: Provider service + adapter + single send + webhook + statuses + polling** (Signed callbacks and status lifecycle exercised E2E; dedupe/order logic also unit-tested)
- [x] **P4: Bulk send with per-recipient results + history screen** (Seeded per-recipient result and history states exercised E2E; polling behavior build-checked)
- [x] **P5: Failure handling + retry (E) + provider health (D)** (Seeded suffix failures, outage, retry, and health status exercised E2E)
- [ ] **P6: Bonus features (A, B, C)**
- [ ] **P7: Design pass vs /design at 360/768/1280**
- [ ] **P8: Tests, final docs/REVIEW.md, README.md, deployment documentation**

### Repository cleanup (15 Oct 2026)
- Moved the assignment, email brief, progress tracker, and review to their requested `docs/` paths; renamed the Figma link note to `design/FIGMA_LINK.md`.
- Removed only the approved scratch request file and log files; added the missing root ignore patterns. Post-cleanup verification passed: backend pytest (7), Django check, provider pytest (4), frontend lint, and frontend build.
