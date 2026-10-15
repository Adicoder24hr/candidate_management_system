ROLE
You are a senior full-stack engineer. Build the "Candidate Communication Platform"
take-home for Hunar.ai. Deadline is tight, so work in phases, verify each phase,
and never stop at "mostly done".

Also read docs/EMAIL_BRIEF.md for stack and submission requirements.

SOURCES OF TRUTH (read first, in this order)
1. docs/ASSIGNMENT.md  – functional requirements (every line is a requirement)
2. /design/*.png and the Figma MCP (if connected) – visual spec
3. design/TOKENS.md (if present) – colors, fonts, radius, spacing
If the design is ambiguous or a screen is missing, DO NOT invent silently:
list the assumption in DECISIONS.md and pick the simplest option consistent
with the design language. Never claim a pixel match you haven't verified.

TECH STACK (fixed)
- Frontend: Next.js (App Router) + React + TypeScript (strict) + Material UI.
  MOBILE-FIRST: write base styles for 360px, then scale up with MUI breakpoints
  (sm 600, md 900, lg 1200). No horizontal scroll at 360px. Touch targets >= 44px.
  Use a single MUI theme built from the design tokens (palette, typography,
  shape.borderRadius, spacing base 8px). No hardcoded colors in components.
- Backend: Python + Django + Django REST Framework.
- Database: MongoDB Atlas via the official `django-mongodb-backend`
  (pin a compatible Django version, document it). Connection via MONGODB_URI in .env.
- Dummy provider: a SEPARATE small Python service in /provider-service
  (own process, own port, own README section). Not imported by the main app.
- Tests: pytest (backend), Vitest/RTL (frontend, key components).

DATABASE CONNECTION (MongoDB Atlas, existing cluster)
- The connection string is ALREADY in backend/.env as MONGODB_URI (database
  name: candidate_comm). Read it from the environment only.
- NEVER hardcode, print, log, or copy the URI or password into any file,
  README, docs/PROGRESS.md, docs/REVIEW.md, DECISIONS.md, test output or chat message.
- Ensure .gitignore excludes .env before the first commit; commit only
  .env.example with placeholders.
- At startup, verify the connection with a ping and fail with a clear message
  if it can't connect (without printing the URI).
- Collections are created automatically by migrations; do not ask me to create
  them manually. Document Atlas setup in README.md using placeholders only.

REPO LAYOUT
/frontend  /backend  /provider-service  /design  /docs
README.md  docs/REVIEW.md  docs/PROGRESS.md  DECISIONS.md  AGENTS.md  .env.example

CORE FEATURES (all required)
1. Candidates: add (validated), list, search (name/phone/email, debounced,
   server-side), detail page. Validation: name required 2-80 chars; phone in
   E.164 (+countrycode...), normalize before saving; email valid; reject
   duplicate phone/email with a clear message (409).
2. Send single message to a candidate.
3. Bulk send: multi-select candidates (select-all, count in button label
   "Send to N Candidates"), one message. Each recipient is its own Message record
   processed independently; one failure never blocks others. After submit show a
   per-candidate result list (sent / failed + human reason), with summary
   "X succeeded, Y failed".
4. Message statuses: scheduled (bonus), queued, sent, delivered, read, failed.
   UI shows the latest status with icon + color + text (not color alone).
5. Status updates via WEBHOOK from provider -> POST /api/webhooks/provider/.
   - Verify HMAC-SHA256 signature header using a shared secret.
   - Idempotent: unique (provider_message_id, provider_event_id); a repeated
     event returns 200 and changes nothing.
   - Out-of-order safe using status rank:
       queued=1, sent=2, delivered=3, read=4. Only move forward (higher rank).
       "failed" is accepted only if current status is queued or sent;
       ignore failed after delivered/read. Every event is still stored in
       message_status_events for the audit trail.
   - Frontend reflects updates by polling every 3s while any visible message is
     non-terminal (terminal = read or failed; stop polling otherwise).
6. Failure handling: map provider errors to friendly messages, never raw errors:
   invalid_recipient -> "This phone number isn't valid or can't receive messages."
   rate_limited      -> "Too many messages sent. We'll retry shortly."
   temporary_failure -> "The messaging service had a temporary problem."
   provider_down     -> "The messaging service is currently unavailable."
   delivery_failed   -> "The message couldn't be delivered to the recipient."
   unknown           -> "Something went wrong. Please try again."
   Store error_code, friendly_message, retryable (bool), attempt_count.
7. Communication history per candidate: newest first; each item shows message
   text, formatted timestamp (e.g. "08 Oct 2026, 10:30 AM", IST), status chip,
   failure reason if any, retry button if retryable.
8. UX states for EVERY screen: loading skeletons, empty candidate list, empty
   history, failed request (inline error + Retry), sending (button disabled +
   spinner, prevent double submit), updating status, bulk results.
   Use snackbars for success/errors, form-level + field-level validation messages.

BONUS (do only after core is verified; implement in this order)
E. Retry: classify retryable = {rate_limited, temporary_failure, provider_down,
   timeout}; permanent = {invalid_recipient, delivery_failed}.
   Auto-retry retryable errors up to 3 times with exponential backoff:
   delay = min(2s * 2^attempt, 30s) + random jitter 0-500ms (attempt starts at 0).
   Manual "Retry" button only for retryable failures; permanent shows
   "Can't be retried: <reason>". Retrying reuses the same Message with an
   idempotency key so no duplicate is sent.
D. Provider health: card with status (Operational / Degraded / Down),
   sent, delivered, failed counts, and success rate = delivered / sent * 100
   (show "-" if sent = 0). Status: Operational if provider /health ok and
   failure rate over last 20 messages < 20%; Degraded 20-50%; Down if health
   check fails or > 50%. If Down, show a banner and disable send with a clear
   explanation (or queue them – document the choice).
A. Templates with placeholders {{name}}, {{email}}, {{phone}}; render per
   candidate at send time; preview in UI; unknown placeholder -> validation error.
B. Scheduled messages: datetime picker (must be in the future, IST),
   status "scheduled", a worker (management command + loop) sends due messages;
   cancel allowed while scheduled.
C. Multiple providers: define a ProviderAdapter interface in backend; implement
   "dummy-whatsapp" and "dummy-email"; user picks channel when sending.
   Statuses/validation depend on channel.

DUMMY PROVIDER SPEC (/provider-service, FastAPI or Flask)
Endpoints: POST /v1/messages (returns provider_message_id), GET /v1/messages/{id},
GET /health, POST /admin/outage {"on": true|false}.
Deterministic behavior by phone number suffix (document in README):
  ends 0000 -> 422 invalid_recipient
  ends 0429 -> 429 rate_limited (include Retry-After)
  ends 0503 -> 503 temporary_failure (succeeds on the 3rd attempt, to prove retry)
  ends 0500 -> accepted, later webhook "failed" with delivery_failed
  anything else -> accepted; webhooks: sent after ~1s, delivered ~3s, read ~6s
  (random jitter). Randomly (20%) send an event twice, and randomly deliver two
  events out of order, to exercise idempotency/ordering.
When outage is on, every call returns 503 provider_down.
Webhooks are signed with HMAC-SHA256 using PROVIDER_WEBHOOK_SECRET and include a
unique event_id. The main app calls the provider with a 5s timeout; timeouts are
treated as retryable.

API (REST, versioned /api/v1/): /candidates (GET list+search+pagination, POST),
/candidates/{id}, /candidates/{id}/messages, /messages (POST single),
/messages/bulk (POST), /messages/{id}/retry, /webhooks/provider, /health/provider,
/templates (bonus). Consistent error shape:
{"error": {"code": "...", "message": "<friendly>", "fields": {...}}}.
Use proper status codes (400/404/409/422/429/503). No stack traces to clients.

ENGINEERING RULES
- Clean layering in backend: views -> services -> provider adapters -> models.
  No business logic in views. Type hints everywhere.
- Frontend: feature folders, typed API client, React Query (or SWR) for data,
  reusable components (StatusChip, EmptyState, ErrorState, ConfirmDialog).
- Environment variables only, provide .env.example for every service. No secrets
  in git. CORS restricted to the frontend origin.
- Accessibility: labels, aria-live for status updates, keyboard navigation.
- Seed script: 8 candidates, including numbers ending 0000, 0429, 0503, 0500.

DOCUMENTATION RULES (continuous, not at the end)
- README.md: overview, architecture diagram (mermaid), prerequisites, exact setup
  steps for all 3 services, MongoDB Atlas setup (db candidate_comm, user, IP
  allowlist, connection string), env var table, how to run tests, how to run the
  demo scenarios (which phone numbers trigger what), deployment steps, assumptions,
  known limitations, bonus features implemented.
- docs/PROGRESS.md: checklist of every requirement with status (todo/in-progress/done/
  verified) and a dated log. Update after EVERY change.
- DECISIONS.md: each architectural decision + reason + alternatives.
- docs/REVIEW.md: after each phase, review your own work like a strict reviewer:
  requirement coverage, edge cases, security, error handling, a11y,
  responsiveness (check 360/768/1280 widths), design mismatches vs /design images,
  bugs found and fixed. List remaining issues honestly.
- Update README/PROGRESS/DECISIONS/REVIEW in the same step as any code change
  that affects them.

PHASES (stop and run the verification at the end of each; do not skip ahead)
P0  Read all sources. Produce docs/PROGRESS.md with the full requirement checklist,
    a screen inventory mapped to design images, and DECISIONS.md assumptions.
P1  Scaffold 3 services, MUI theme from tokens, Mongo connection, health endpoints.
P2  Candidates (backend + UI) with validations and all UX states.
P3  Provider service + adapter + single send + webhook + statuses.
P4  Bulk send with per-recipient results + history screen + polling.
P5  Failure handling + retry (E) + provider health (D).
P6  Remaining bonus (A, B, C) only if P1-P5 are verified.
P7  Design pass: compare each screen to its /design image at mobile and desktop
    widths (use the browser tool to screenshot if available), fix mismatches.
P8  Tests, final docs/REVIEW.md, README polish, deployment instructions.

VERIFICATION AFTER EACH PHASE
Run the backend tests, the frontend type-check/lint/build, and exercise the
feature end to end against the real services (use the seeded phone numbers to
trigger every failure path). Report what you actually ran and the results.
Never mark an item "verified" unless you ran it.

OUTPUT STYLE
Be concise in chat. After each phase give: what changed, what was verified,
what's open. If blocked or the design is unclear, ask ONE precise question,
and meanwhile continue with the best-documented assumption.
