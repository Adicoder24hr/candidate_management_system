# Architecture Decisions & Design System Baseline (DECISIONS.md)

**Project**: Candidate Communication & Management System  
**Date**: October 2026  
**Status**: Revised per P0 Review — Executing  

## 0. Audit Clarifications (15 Oct 2026)

- The assignment and email brief are stored at `docs/ASSIGNMENT.md` and `docs/EMAIL_BRIEF.md`.
- No `design/TOKENS.md` exists. The mockup notes are the available token source; mobile behavior is an assumption because no mobile frames exist.
- The candidate table uses responsive MUI layout, candidate names open history, and soft-delete confirmation preserves history. This follows the available mockups; no mobile screenshot comparison has been completed.
- When provider health reports `down`, sending is disabled and an inline explanation is shown; this follows the assignment's allowed disable-or-queue choice and avoids implying a message was accepted.
- Django and provider signing secrets have no code defaults; both are required in their process environments so the checked-in source contains no reusable secret.

---

## 1. Stack Choices & Technical Architecture

### 1.1 Frontend
- **Framework**: Next.js 14/15 (App Router, TypeScript strict mode).
- **UI Library**: Material UI (MUI v5/v6) with Emotion.
- **Icons**: MUI Icons (`@mui/icons-material`) and Lucide React.
- **Responsiveness**: Mobile-first responsive layout (360px minimum width up to 4K desktop). Touch targets >= 44px.
- **Design Alignment**: Closely matches the Figma, verified by screenshots in the design pass (P7).

### 1.2 Backend
- **Framework**: Python + Django 5.x with Django REST Framework (DRF).
- **Database Backend**: MongoDB Atlas via `django-mongodb-backend` (database: `candidate_comm`).
  - *Python 3.14 Compatibility Decision*: Time-boxed testing of `django-mongodb-backend`. If compatibility issues arise on Python 3.14, cleanly fall back to Django + DRF with a robust PyMongo repository layer or Python 3.12/3.13 if available.
- **API Architecture**: Versioned REST API (`/api/v1/`).
- **Security & Integrity**:
  - `MONGODB_URI` read from environment only. Never printed, hardcoded, or logged.
  - Startup database ping to fail fast with a friendly message if connection fails.
  - HMAC-SHA256 signature verification on provider webhook endpoints (`X-Provider-Signature` header using `PROVIDER_WEBHOOK_SECRET`).
  - Idempotent webhook processing to safely handle repeated/duplicate events.
  - CORS restricted to the frontend origin (`http://localhost:3000`).

### 1.3 Dummy Provider Service
- **Location**: Standalone service in `/provider-service` (own process, own port 8001, own README section).
- **Runtime**: FastAPI or lightweight ASGI/HTTP service.
- **Deterministic Endpoints & Behavior**:
  - `POST /v1/messages` (returns `provider_message_id`)
  - `GET /v1/messages/{id}`
  - `GET /health`
  - `POST /admin/outage` with payload `{"on": true|false}` (returns 503 `provider_down` when active)
  - **Deterministic behavior by phone suffix**:
    - ends `0000` -> 422 `invalid_recipient`
    - ends `0429` -> 429 `rate_limited` (includes `Retry-After: 5`)
    - ends `0503` -> 503 `temporary_failure` (succeeds on the 3rd attempt to demonstrate auto-retry)
    - ends `0500` -> accepted (202), then subsequent webhook callback with `delivery_failed`
    - anything else -> accepted (202); webhooks dispatched: `sent` after ~1s, `delivered` after ~3s, `read` after ~6s (with random jitter).
    - Simulates 20% duplicate events and random out-of-order events to test backend idempotency and status rank monotonicity.

---

## 2. Design System Tokens & Visual Extensions

| Category | Token / Element | Value | Usage |
|---|---|---|---|
| **Color** | `primary.main` | `#1976D2` | Active buttons, full name links, send icons |
| **Color** | `primary.dark` | `#1565C0` | Button hover states |
| **Color** | `primary.light` | `#EBF3FE` | Selected row highlight |
| **Color** | `status.read.bg` | `#E8F5E9` | "read" chip background |
| **Color** | `status.read.text` | `#2E7D32` | "read" chip label & checkmarks |
| **Color** | `status.delivered.bg` | `#E0F2F1` | "delivered" chip background (Assumed token) |
| **Color** | `status.delivered.text` | `#00796B` | "delivered" chip label & checkmark (Assumed token) |
| **Color** | `status.sent.bg` | `#E3F2FD` | "Sent" chip background |
| **Color** | `status.sent.text` | `#1976D2` | "Sent" chip label |
| **Color** | `status.failed.bg` | `#FFEBEE` | "Failed" chip background |
| **Color** | `status.failed.text` | `#D32F2F` | "Failed" chip label & exclamation icon |
| **Color** | `status.na.text` | `#757575` | "NA" uncontacted label |
| **Color** | `danger.main` | `#D32F2F` | Delete buttons, destructive dialog actions |
| **Color** | `border.default` | `#E0E0E0` | Table cell borders, dividers |
| **Color** | `toast.success.bg` | `#EDF7ED` | Success snackbar background |
| **Color** | `toast.success.text`| `#1E4620` | Success snackbar text |
| **Typography**| Font Family | `Inter, Roboto, sans-serif` | Clean, modern sans-serif |
| **Component** | Status Chip | `border-radius: 16px`, height `24px` | Pill status badges |
| **Component** | Recipient Chip | `border-radius: 16px`, height `28px` | Removable chips with delete cross icon |
| **Component** | Sliding Drawer | `width: 480px` (desktop), `100vw` (mobile) | Right anchored slide-in form |
| **Component** | Resizable Textarea | CSS `resize: vertical`, min-height `120px` | Message textarea per dev note |

---

## 3. Data Model Architecture

### 3.1 Candidate Model (`Candidate`)
```json
{
  "_id": "ObjectId",
  "candidate_id": "String (unique 6-char alphanumeric, e.g. 'A1B2C3')",
  "name": "String (2-80 characters, validated)",
  "phone": "String (E.164 normalized, e.g. '+919876543210')",
  "email": "String (RFC compliant, lowercase)",
  "created_at": "ISODate",
  "updated_at": "ISODate",
  "is_deleted": "Boolean (default: false)"
}
```
*Note*: Uniqueness constraint on `phone` and `email` applies only to active records where `is_deleted == false`. Deletion is soft delete to preserve historical communication logs.

### 3.2 Message Model (`Message`)
```json
{
  "_id": "ObjectId",
  "message_id": "String (UUID v4)",
  "body": "String",
  "channel": "String (e.g. 'whatsapp' | 'email')",
  "scheduled_at": "ISODate (optional, null if immediate)",
  "created_at": "ISODate"
}
```

### 3.3 MessageRecipient Model (`MessageRecipient`)
```json
{
  "_id": "ObjectId",
  "message_id": "ObjectId (ref: Message)",
  "candidate_id": "ObjectId (ref: Candidate)",
  "status": "String (queued | sent | delivered | read | failed | scheduled)",
  "channel": "String (whatsapp | email)",
  "provider_message_id": "String (returned by provider)",
  "error_code": "String (invalid_recipient | rate_limited | temporary_failure | provider_down | delivery_failed | unknown)",
  "friendly_message": "String (Human-friendly error explanation)",
  "retryable": "Boolean",
  "attempt_count": "Integer (default: 1)",
  "idempotency_key": "String (UUID)",
  "sent_at": "ISODate",
  "delivered_at": "ISODate",
  "read_at": "ISODate",
  "failed_at": "ISODate"
}
```

### 3.4 WebhookEvent Model (`WebhookEvent`)
```json
{
  "_id": "ObjectId",
  "event_id": "String (unique)",
  "provider_message_id": "String",
  "status": "String",
  "signature": "String",
  "payload": "Object",
  "received_at": "ISODate",
  "processed": "Boolean"
}
```

---

## 4. Status Progression & Failure Handling

### 4.1 State Monotonicity
- Ranks: `queued` = 1, `sent` = 2, `delivered` = 3, `read` = 4.
- Only forward progression is permitted.
- `failed` is accepted **only** if the current status is `queued` or `sent`. Late `failed` events after `delivered` or `read` are rejected and recorded for audit only.
- Terminal statuses: `read` and `failed`.
- Frontend polls `GET /api/v1/candidates/{id}/messages` every 3s as long as any visible message is non-terminal.

### 4.2 Failure Mapping Dictionary
| Error Code | Friendly User Message | Retryable |
|---|---|---|
| `invalid_recipient` | This phone number isn't valid or can't receive messages. | No (Permanent) |
| `rate_limited` | Too many messages sent. We'll retry shortly. | Yes |
| `temporary_failure` | The messaging service had a temporary problem. | Yes |
| `provider_down` | The messaging service is currently unavailable. | Yes |
| `delivery_failed` | The message couldn't be delivered to the recipient. | No (Permanent) |
| `unknown` | Something went wrong. Please try again. | Yes |

---

## 5. Explicit Design Assumptions

1. **Delivered Status Chip**: The Figma mockups show `read` (green), `Sent` (blue), `Failed` (red), and `NA` (gray), but omit an explicit mockup for `delivered`. We adopt a subtle teal/cyan chip (`#E0F2F1` background, `#00796B` text) with a single checkmark icon to harmoniously fit the design system.
2. **Mobile Viewport (360px)**: The Figma does not include mobile frames. For 360px:
   - The table utilizes smooth horizontal scrolling with sticky column styling and 44px touch targets.
   - Drawers and dialogs expand to full width (`100vw`) with compact padding to eliminate horizontal scroll.
3. **Timestamps**: All timestamps represent Indian Standard Time (IST, UTC+05:30) and are formatted as `DD-MM-YYYY | H:MM AM/PM` (e.g., `25-10-2026 | 9:47 AM`).
4. **Table "Last Message" Column**: Derived dynamically from the timestamp of the latest communication sent to that candidate (or `NA` if none).
5. **Bulk Send Failure View**: If a bulk send succeeds for all candidates, the Figma toast (`Message sent to N candidates`) is displayed. If any recipients fail, a per-candidate results drawer/dialog displays a summary ("X succeeded, Y failed") with candidate name and friendly failure reason for each failed recipient.

---

## 6. Seed Data Plan

Includes the 7 Figma candidates, plus the 4 deterministic test candidates:

| Candidate ID | Name | Phone (E.164) | Email | Suffix Role / Initial State |
|---|---|---|---|---|
| `A1B2C3` | Krishna Khandelwal | `+919876543210` | `krishna.khandelwal@gmail.com` | Figma `read` (12-10-2026) |
| `D4E5F6` | Urvashi Soni | `+919123456789` | `urvashi.soni@gmail.com` | Figma `failed` (15-10-2026) |
| `G7H8I9` | Aditya Kumar | `+919988766554` | `aditya.kumar@gmail.com` | Figma `read` (18-10-2026) |
| `J1K2L3` | Ajit Srivastava | `+919234567890` | `ajit.srivastava@gmail.com` | Figma `read` (21-10-2026) |
| `M4N5O6` | Aniket Sawant | `+919876512345` | `aniket.sawant@gmail.com` | Figma `sent` (24-10-2026) |
| `P7Q8R9` | Ira Akbar | `+919456789012` | `ira.akbar@gmail.com` | Figma `NA` |
| `S1T2U3` | Amarjeet Kumar | `+919012345678` | `amarjeet.kumar@gmail.com` | Figma `NA` |
| `T0E000` | Vikram Test-Invalid | `+919876500000` | `vikram.0000@test.com` | **0000**: 422 `invalid_recipient` |
| `T0E429` | Priya Test-RateLimit | `+919876500429` | `priya.0429@test.com` | **0429**: 429 `rate_limited` |
| `T0E503` | Rohan Test-TempFail | `+919876500503` | `rohan.0503@test.com` | **0503**: 503 `temporary_failure` (3rd retry passes) |
| `T0E500` | Neha Test-DeliveryFail | `+919876500500` | `neha.0500@test.com` | **0500**: Webhook `delivery_failed` |
| *Plus 20+* | Overflow Candidates | Various valid | Various valid | Triggers `+24` chip overflow |
