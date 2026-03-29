# Reimbursement Management System - Phase Breakdown

This phase plan is derived from the full PRD in other/prd.md and aligned to the hackathon delivery order.

## Phase 1 - Auth and Company Bootstrap (Implemented in this commit)

Scope:
- Backend auth foundation with JWT access/refresh tokens.
- First-time signup that creates Company + Admin user in one transaction.
- Country to base-currency mapping during signup.
- Login and token refresh endpoints.
- Current user endpoint for session bootstrap.
- Frontend login/signup pages with validation and API integration.
- Protected app shell with sidebar/header and role-aware landing.

Deliverables:
- FastAPI backend project scaffold with SQLAlchemy models for Company and User.
- React + Vite frontend scaffold with auth context, route guards, and minimal dashboard shell.

Acceptance:
- New admin can signup with company details and receive tokens.
- Existing user can login and access protected screen.
- Refresh endpoint issues a new access token.
- Authenticated request to /users/me returns profile and company.

## Phase 2 - Core Models and Migrations (Implemented)

Scope:
- Add all primary entities from PRD section 4.
- Add Alembic migration setup and first complete migration set.
- Seed baseline categories per company bootstrap.

Acceptance:
- Schema supports entities in section 4 with constraints/indexes.
- New company gets default categories.

## Phase 3 - Employee Claim Lifecycle (Draft and Submit) (Implemented)

Scope:
- Claim create/update/list/detail endpoints for employee.
- Draft and submit flows with transition validation.
- Employee dashboard and my-claims table with status filters.

Acceptance:
- Employee can create draft, edit draft, and submit claim.
- Claims list supports status/date filtering.

## Phase 4 - Approval Engine and Approver Inbox (Implemented)

Scope:
- Approval task generation from rules or manager fallback.
- Approver inbox and claim detail for review.
- Approve/reject actions and status transitions.

Acceptance:
- Submitted claim creates approval tasks.
- Approver can approve/reject and status progression is correct.

## Phase 5 - Admin Master Data (Implemented)

Scope:
- User management (create/edit/deactivate).
- Department management.
- Category management.

Acceptance:
- Admin can CRUD users/departments/categories with RBAC enforcement.

## Phase 6 - Approval Rule Management (Implemented)

Scope:
- Rule CRUD and rule step configuration.
- Sequential and minimum-approval strategies.
- Rule matching by amount/category/department and priority.

Acceptance:
- Admin can configure and activate rules.
- Engine picks highest-priority matching active rule.

## Phase 7 - Receipt Upload and OCR (Implemented)

Scope:
- Receipt upload APIs and file storage abstraction.
- OCR extraction persistence and parsed suggestions.
- Frontend prefill UX for submit expense form.

Acceptance:
- Uploading a receipt returns OCR output and prefills fields.

## Phase 8 - Currency Conversion and Snapshots (Implemented)

Scope:
- Exchange-rate service and snapshot model usage.
- Conversion at submit time and preview endpoint.

Acceptance:
- Submitted claims store conversion snapshot and converted amount.

## Phase 9 - Audit, Hardening, and Demo Polish

Scope:
- Audit logs and timeline enhancements.
- Error handling consistency, pagination, perf passes.
- Demo script and quality pass for hackathon.

Acceptance:
- End-to-end demo scenario in PRD section 11 runs without manual DB edits.
