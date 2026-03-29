# Reimbursement Management System – Product Requirements Document (PRD)

## 1. Overview

The Reimbursement Management System is a web application that streamlines employee expense reimbursements by digitizing submission, approval, and audit workflows.[page:1] It targets organizations that currently rely on manual, spreadsheet- or email-based reimbursement processes that are slow, error-prone, and non-transparent.[page:1] The system provides configurable approval rules, multi-level approvals, and automatic currency conversion into a company’s base currency, while remaining implementable within a time-bound hackathon.

This PRD is written for a coding assistant (and developers) who will implement a **React + Vite** frontend, a **FastAPI** backend, and a **PostgreSQL** database, with a focus on a strong hackathon-ready product rather than full enterprise coverage.[page:1] The design follows the provided mockups, which include separate views for Admin (company setup and rules), Employee (expense submission and history), and Manager/Approver (approvals queue).[file:2]

### 1.1 Goals

- Digitize reimbursement submission and approval with clear, auditable status tracking.
- Allow companies to define approval flows based on **amount thresholds** and **other rules**, while also leveraging the **reporting manager** hierarchy as a fallback.[page:1]
- Support **multi-level approvals** and **minimum-approval percentage** logic per rule where applicable.[file:2]
- Automatically **create a Company and Admin user** on first signup and set the company’s base currency from the environment/country selection.[page:1]
- Extract key fields from receipt images using OCR and pre-fill expense details, allowing users to review and correct before submitting.
- Provide simple, responsive UIs for employees, approvers, and admins that match the hackathon mockups.[file:2]

### 1.2 Non-Goals (V1)

- Complex accounting integration (ERP, payroll systems).
- Multi-line-item claims (V1 uses one expense per claim for implementation speed).
- Advanced analytics, budgeting, or fraud detection beyond basic reports and logs.
- Full-fledged notification infrastructure (use in-app indicators only in V1).

---

## 2. System Architecture

### 2.1 High-Level Architecture

The system uses a typical SPA + API split:

- **Frontend**
  - React + Vite.
  - TypeScript (recommended but not absolutely required).
  - UI built as modular feature areas: Auth, Employee, Approvals, Admin.[file:2]
- **Backend**
  - FastAPI for REST APIs and OpenAPI schema.
  - SQLAlchemy + Alembic for ORM and migrations.
  - Separate modules for auth, companies, users, departments, categories, claims, receipts, OCR, approval rules, approvals, exchange rates, and audit.[page:1]
- **Database**
  - PostgreSQL as the primary data store.
- **Storage**
  - Local file system storage for receipt images for the hackathon (abstracted so it can be swapped for S3 later).
- **OCR**
  - OCR service abstraction:
    - Primary: integration-ready for external OCR APIs (e.g., Google Vision).
    - Fallback: local Tesseract if available.
- **Deployment / Dev**
  - Local development: Docker Compose recommended (Postgres + backend + frontend).
  - For hackathon demo: can be run locally or deployed to a simple cloud environment (e.g., Railway/Render/Heroku-like).

### 2.2 Module Boundaries (Backend)

Recommended FastAPI application package structure:

- `app/main.py` – FastAPI app startup, router registration.
- `app/core/` – settings, config, logging, security (JWT utilities).
- `app/db/` – SQLAlchemy base, session, migrations (Alembic scripts).
- `app/models/` – ORM models for all entities.
- `app/schemas/` – Pydantic request/response models.
- `app/api/` – routers grouped by feature:
  - `auth.py`
  - `companies.py`
  - `users.py`
  - `departments.py`
  - `categories.py`
  - `claims.py`
  - `receipts.py`
  - `ocr.py`
  - `approval_rules.py`
  - `approvals.py`
  - `exchange_rates.py`
  - `audit.py`
- `app/services/` – business logic/services:
  - `approval_engine.py` (rule evaluation + manager fallback).
  - `ocr_service.py` (OCR abstraction).
  - `currency_service.py` (exchange rate retrieval + conversion).
  - `notification_service.py` (in-app only for V1).
- `app/dependencies/` – FastAPI dependency functions (auth, db session, permission checks).

### 2.3 Module Boundaries (Frontend)

Suggested folder structure:

- `src/main.tsx` – React entry, router setup.
- `src/app/` – root layout, providers.
- `src/features/`
  - `auth/` – login, signup, logout flows.
  - `employee/`
    - `Dashboard`
    - `SubmitExpense`
    - `MyClaims`
  - `approvals/`
    - `ApprovalsInbox`
    - `ClaimDetailView`
  - `admin/`
    - `CompanySettings`
    - `UserManagement`
    - `DepartmentManagement`
    - `CategoryManagement`
    - `RuleManagement`
  - `shared/`
    - components (Tables, Forms, Modals, Toasts, etc.)
    - hooks (useAuth, useApi, usePagination, useFilters).
- `src/api/` – API client wrappers for each backend module.
- `src/types/` – shared type definitions.

Routing (e.g., using React Router):

- `/login`, `/signup`
- `/employee/dashboard`, `/employee/claims`, `/employee/submit`
- `/approvals/inbox`, `/approvals/claim/:id`
- `/admin/settings`, `/admin/users`, `/admin/departments`, `/admin/categories`, `/admin/rules`

---

## 3. User Roles & Permissions

### 3.1 Roles

V1 defines three core roles:

- **Admin**
  - Owns company configuration.
  - Manages users and departments.
  - Defines categories and approval rules.
  - Can view all claims and approvals for the company.
- **Employee**
  - Creates and manages expense claims (draft, submit, resubmit).
  - Views personal claim history and statuses.
- **Approver**
  - Reviews claims assigned by rules or as reporting manager.
  - Approves or rejects claims and leaves comments.
  - Can see only claims where they are part of the approval chain.

Role mapping:

- Every user has a **base role** (ADMIN or EMPLOYEE) and an **is_approver** flag.
- Many admins may also be marked as approvers.
- Reporting-manager hierarchy is represented as `manager_id` on `User`.

### 3.2 Permission Matrix

| Action                                                 | Admin | Employee | Approver |
|--------------------------------------------------------|-------|----------|----------|
| Signup first company                                   | Yes   | No       | No       |
| Invite/create users                                    | Yes   | No       | No       |
| Create/edit departments                                | Yes   | No       | No       |
| Create/edit categories                                 | Yes   | No       | No       |
| Create approval rules                                  | Yes   | No       | No       |
| Submit expense claim                                   | No    | Yes      | No       |
| Save draft expense claim                               | No    | Yes      | No       |
| Edit claim before first approval                      | No    | Yes (own)| No       |
| Resubmit rejected claim                                | No    | Yes (own)| No       |
| View own claims                                        | No    | Yes      | No       |
| View all company claims                                | Yes   | No       | No       |
| View assigned approvals                                | Yes*  | No       | Yes      |
| Approve/reject assigned claims                         | Yes*  | No       | Yes      |
| View audit log                                         | Yes   | No       | No       |

\*Admins can be configured as approvers and thus see approval queues when `is_approver` is true.

---

## 4. Core Domain Model

### 4.1 Entity List

- Company
- Department
- User
- ExpenseCategory
- ExpenseClaim
- ReceiptFile
- OCRExtraction
- ApprovalRule
- ApprovalRuleStep
- ApprovalTask
- ApprovalActionLog
- ExchangeRateSnapshot
- AuditLog

### 4.2 Entity Definitions and Fields

#### 4.2.1 Company

Represents an organization/tenant.

- `id` (UUID / bigserial)
- `name` (string, required)
- `country_code` (string, ISO 3166-1 alpha-2, e.g., "IN")
- `base_currency` (string, ISO 4217, e.g., "INR") – determined at signup per problem statement.[page:1]
- `created_at` (timestamp)
- `updated_at` (timestamp)

Constraints:
- Unique `(name)` per environment.
- `base_currency` is immutable after initial setup in V1.

#### 4.2.2 Department

Lightweight grouping for rule targeting.

- `id`
- `company_id` (FK → Company)
- `name` (string)
- `code` (string, optional, unique per company)
- `created_at`
- `updated_at`

#### 4.2.3 User

Application users.

- `id`
- `company_id` (FK)
- `email` (unique per company)
- `hashed_password`
- `first_name`
- `last_name`
- `role` (enum: `ADMIN`, `EMPLOYEE`)
- `is_approver` (bool)
- `department_id` (FK → Department, nullable)
- `manager_id` (FK → User, nullable) – reporting manager for fallback approvals.
- `is_active` (bool)
- `created_at`
- `updated_at`

Indexes:
- `company_id`, `email`.
- `manager_id`.

#### 4.2.4 ExpenseCategory

Reimbursement categories.

- `id`
- `company_id`
- `name` (e.g., "Travel", "Food", "Accommodation")
- `code` (string, optional)
- `description` (text, optional)
- `is_active` (bool)
- `created_at`
- `updated_at`

V1 seeding:
- On first company creation, the system seeds default categories (e.g., Travel, Food, Office, Misc). Admins can edit/add categories.[page:1]

#### 4.2.5 ExpenseClaim

Main entity for an individual expense.

- `id`
- `company_id`
- `employee_id` (FK → User)
- `category_id` (FK → ExpenseCategory)
- `department_id` (denormalized from employee at submission time)
- `title` (short description)
- `description` (long text)
- `receipt_file_id` (FK → ReceiptFile, nullable until upload)
- Monetary fields:
  - `original_currency` (e.g., USD, INR)
  - `original_amount` (decimal)
  - `base_currency` (copy from company for the claim)
  - `converted_amount` (decimal)
  - `exchange_rate_snapshot_id` (FK → ExchangeRateSnapshot)
- Dates:
  - `expense_date` (date)
  - `submitted_at` (timestamp, nullable)
  - `final_approved_at` (timestamp, nullable)
- Status:
  - `status` (enum: `DRAFT`, `SUBMITTED`, `IN_REVIEW`, `APPROVED`, `REJECTED`, `CANCELLED`)
  - `current_approval_step` (int, nullable)
  - `is_resubmission` (bool, default false)
  - `rejection_reason` (string, optional – last rejection)
- `created_at`
- `updated_at`

Rules:
- One `ExpenseClaim` corresponds to one primary receipt / expense item in V1.
- Convert currency at submission (or at first submit if previously draft).

#### 4.2.6 ReceiptFile

Metadata about uploaded receipts.

- `id`
- `company_id`
- `employee_id`
- `file_path` (string – local path)
- `original_filename`
- `file_mime_type`
- `file_size_bytes`
- `uploaded_at`

#### 4.2.7 OCRExtraction

Result of OCR processing for a given receipt.

- `id`
- `receipt_file_id` (FK)
- `raw_text` (text)
- `parsed_fields` (JSONB), e.g.,
  - `merchant_name`
  - `amount`
  - `currency`
  - `date`
  - `tax_amount`
  - `line_items` (optional)
- `confidence` (float 0–1)
- `engine` (string: `"tesseract"`, `"google_vision"`, etc.)
- `created_at`

Usage:
- When user uploads a receipt, backend triggers OCR, populates `OCRExtraction`, and returns parsed suggestions for the employee to confirm/edit before finalizing the claim.

#### 4.2.8 ApprovalRule

Defines a policy that determines how claims are routed.

- `id`
- `company_id`
- `name`
- `description`
- Scope & conditions:
  - `min_amount` (decimal, nullable)
  - `max_amount` (decimal, nullable)
  - `category_id` (FK, nullable – rule can be category-specific)
  - `department_id` (FK, nullable)
- Evaluation behavior:
  - `strategy` (enum: `SEQUENTIAL`, `MIN_APPROVALS`)
  - `min_approval_percentage` (int 0–100, used by `MIN_APPROVALS` to indicate required fraction of approvers, reflecting mockup “minimum approval percentage” slider.[file:2])
- Generic flags:
  - `is_active` (bool)
  - `priority` (int – lower number = higher priority, used when multiple rules match)
- `created_at`
- `updated_at`

#### 4.2.9 ApprovalRuleStep

Defines the sequence or group of approvers within a rule.

- `id`
- `rule_id` (FK → ApprovalRule)
- `step_order` (int, ≥ 1)
- `name` (e.g., "Manager Approval", "Finance Approval")
- Target approvers:
  - `approver_user_id` (FK → User, nullable)
  - `approver_role` (enum: `MANAGER`, `DEPARTMENT_HEAD`, `SPECIFIC_USER`, etc., for V1 only `MANAGER`, `SPECIFIC_USER` are required)
  - `approver_department_id` (FK, optional for department-based approvers)
- `created_at`
- `updated_at`

Evaluation:
- Sequential: each step must complete before moving to the next.
- Min-approvals: all steps are considered as a group, and each step may have internal grouping, but in V1 keep grouping simple (one approver per step or manager-based).

#### 4.2.10 ApprovalTask

Concrete approval step generated for an `ExpenseClaim` at submission.

- `id`
- `claim_id` (FK → ExpenseClaim)
- `rule_id` (FK → ApprovalRule, nullable if fallback)
- `rule_step_id` (FK → ApprovalRuleStep, nullable if fallback)
- `approver_id` (FK → User)
- `sequence_order` (int) – the order claims should be evaluated.
- `status` (enum: `PENDING`, `APPROVED`, `REJECTED`, `SKIPPED`)
- `acted_at` (timestamp, nullable)
- `acted_by` (FK → User, nullable – in case admin overrides)
- `comment` (text, nullable)
- `created_at`

Constraints:
- For sequential rules, only tasks with the minimum `sequence_order` among `PENDING` tasks are actionable.
- For `MIN_APPROVALS` strategy, track count of `APPROVED` tasks and compare to required count/percentage.

#### 4.2.11 ApprovalActionLog

Timeline of actions for each claim.

- `id`
- `claim_id`
- `actor_id` (User)
- `action_type` (enum: `SUBMITTED`, `RESUBMITTED`, `APPROVED`, `REJECTED`, `COMMENTED`, `RULE_MATCHED`, `FALLBACK_MANAGER_USED`)
- `task_id` (FK → ApprovalTask, nullable)
- `description` (text)
- `created_at`

This supports auditability and UI timeliness/status history.

#### 4.2.12 ExchangeRateSnapshot

Captures the rate used for conversion.

- `id`
- `base_currency`
- `foreign_currency`
- `rate` (decimal, e.g., base = INR, foreign = USD, rate = INR per USD)
- `provider` (string – "ECB", "Custom", etc.)
- `as_of` (timestamp)
- `created_at`

Approach:
- For hackathon, a simple rate provider can be mocked/hardcoded or fetched via free API; but the PRD assumes a pluggable service.

#### 4.2.13 AuditLog

System-wide event logs.

- `id`
- `company_id`
- `user_id` (nullable – system events)
- `event_type` (enum, e.g., `USER_CREATED`, `ROLE_CHANGED`, `RULE_CREATED`, `RULE_UPDATED`, `CLAIM_STATUS_CHANGED`, `LOGIN_FAILED`)
- `entity_type` (string)
- `entity_id` (string/UUID)
- `metadata` (JSONB)
- `created_at`

---

## 5. Workflow Design

### 5.1 Authentication & Company Bootstrap

**Scenario: First-time signup**

1. User lands on the signup page.
2. User provides:
   - Name
   - Email
   - Password
   - Company name
   - Country / environment country (derives base currency).[page:1]
3. Backend:
   - Creates new Company with `base_currency` derived from country or environment default.
   - Creates Admin User linked to Company with role `ADMIN`.
   - Returns JWT tokens (access + refresh) and user/company context.

**Subsequent logins:**

- Standard email/password login returning tokens.
- Password hashing via a secure algorithm (e.g., bcrypt).
- Token payload includes:
  - `user_id`, `company_id`, `role`, `is_approver`.

### 5.2 Employee Expense Submission

**Main states:**

- `DRAFT` → `SUBMITTED` → `IN_REVIEW` → `APPROVED` or `REJECTED`.

**Flow:**

1. Employee clicks "New Expense" from Employee Dashboard.
2. Employee optionally uploads receipt first:
   - Frontend POSTs to `/api/receipts/` with file.
   - Backend stores file, triggers OCR (async or sync in V1).
   - Backend returns OCRExtraction with parsed suggestions (amount, currency, date, merchant).
3. Frontend pre-fills the form using parsed values; employee can edit:
   - Title
   - Category (select).
   - Amount and currency (original).
   - Expense date.
   - Description/notes.
4. Employee clicks:
   - **Save Draft**: claim stored as `DRAFT`, no approval tasks created.
   - **Submit**: 
     - Backend:
       - Validates required fields.
       - Computes `converted_amount` using `ExchangeRateSnapshot`:
         - If no rate available for `(company.base_currency, original_currency)`, returns error or uses default fallback.
       - Creates `ExpenseClaim` with status `SUBMITTED` and sets `submitted_at`.
       - Triggers **Approval Engine** to generate `ApprovalTask` records.
       - Sets `status = IN_REVIEW`.
       - Creates `ApprovalActionLog` entry `SUBMITTED`.
5. Frontend redirects to Claim Detail or My Claims list.

### 5.3 Approval Engine

The approval engine implements the **Hybrid Model**:

- Step 1: Find matching active `ApprovalRule` for claim.
  - Filter by `company_id`.
  - Amount between `min_amount` and `max_amount` if set.
  - Matching `category_id` and/or `department_id` if specified.
  - Evaluate `priority` (lowest numeric wins).
- Step 2: If rule found:
  - Use `ApprovalRuleStep` records in `step_order` order to generate `ApprovalTask`s.
  - For steps with `approver_role = MANAGER`:
    - Use employee’s `manager_id` as approver.
    - If none, fallback to fallback manager or admin approach (e.g., company admin).
  - For steps with `approver_user_id`, assign that specific user.
- Step 3: If no rule matches:
  - Fallback: create one `ApprovalTask` assigned to employee’s `manager_id`.
- Step 4: For `SEQUENTIAL` rules:
  - Mark all tasks `PENDING` initially.
  - Claim’s `current_approval_step` set to minimum `sequence_order`.
- Step 5: For `MIN_APPROVALS` rules:
  - Approval completion occurs once the number of `APPROVED` tasks meets or exceeds the threshold derived from `min_approval_percentage` or explicit count.
  - Claims can move to `APPROVED` even if some tasks remain `PENDING`; remaining tasks should be auto-marked as `SKIPPED`.

Engine ensures:
- Snapshotting: Approval tasks only created once at submission; rule edits later do not affect existing claims.
- All actions recorded in `ApprovalActionLog`.

### 5.4 Approver Workflow

**Scenario: Approver seeing pending approvals**

1. Approver navigates to Approvals Inbox.
2. Frontend calls `/api/approvals/tasks?status=pending`:
   - Returns tasks where `approver_id = current_user_id` and `status = PENDING`.
   - For sequential rules, backend ensures only tasks at allowable sequence are returned.
3. Approver clicks a task:
   - Opens Claim Detail with:
     - Claim data + currency info.
     - Receipt preview.
     - OCR extracted text.
     - Approval history so far (from `ApprovalActionLog`).
4. Approver chooses **Approve** or **Reject** (with comment required on rejection):
   - Backend:
     - Updates `ApprovalTask.status` to `APPROVED` or `REJECTED`.
     - Sets `acted_at`, `comment`.
     - Logs `ApprovalActionLog`.
     - Runs engine’s next-step logic:
       - Sequential:
         - If `REJECTED`, mark claim `REJECTED`, set `rejection_reason`, mark any remaining pending tasks as `SKIPPED`.
         - If `APPROVED` and more steps remain, set `current_approval_step` to next step; ensure next step tasks become actionable.
         - If `APPROVED` and no further steps, mark claim `APPROVED` and set `final_approved_at`.
       - Min-approvals:
         - Count approved tasks, compare with required threshold; if reached, mark claim `APPROVED` and skip remaining tasks.
5. Frontend updates UI to show success and remove task from approver’s inbox.

### 5.5 Employee Resubmission

**Scenario: Claim rejected**

1. Employee sees claim with status `REJECTED` in My Claims.
2. Claim detail shows last rejection reason and comments from approver(s).
3. Employee can:
   - Edit permitted fields (title, description, amount, category, receipt).
   - Optionally upload a new receipt.
4. On resubmitting:
   - Backend:
     - Marks previous `ApprovalTask`s as historical (status remains as previously set).
     - Creates NEW `ApprovalTask`s via engine (fresh workflow).
     - Sets `status = IN_REVIEW`, `is_resubmission = true`, `rejection_reason` cleared.
     - Adds `ApprovalActionLog` entry `RESUBMITTED`.

---

## 6. Frontend UX Requirements

### 6.1 General UX Principles

- Responsive layout suitable for 1280px desktop and 375px mobile.
- Single-page navigation with visible header showing:
  - Company name.
  - Current user name.
  - Role/role badge.
  - Logout button.
- Dark mode is optional for hackathon; can be postponed.

### 6.2 Authentication Screens

#### 6.2.1 Login

Fields:
- Email
- Password

Actions:
- Login button.
- Link to Signup.

Validation:
- Basic client-side required checks.
- On backend error, show inline error.

#### 6.2.2 Signup (First Company)

Fields:
- Company name
- Country (dropdown)
- Admin name
- Email
- Password / Confirm password

Behavior:
- Country auto-selects base currency (UI shows currency code).
- On submit, call `/auth/signup` to create Company + Admin.

### 6.3 Employee View

#### 6.3.1 Employee Dashboard

Shows:
- Quick stats:
  - Total claims submitted (current month).
  - Approved / Pending / Rejected counts.
- Recent claims list (table):
  - Date
  - Category
  - Amount (original + base currency)
  - Status
  - Last updated.

Actions:
- Button: "Submit New Expense" (leading to submit form).

#### 6.3.2 Submit Expense Form

Fields:
- Upload receipt (file input).
- Title (text).
- Category (select).
- Amount (number) + currency (select; defaults to company base or OCR-detected currency).
- Expense date (date picker).
- Description (textarea).

Behavior:
- On receipt upload, show preview and spinner while OCR runs.
- Pre-fill amount, date, merchant if OCR returns data; highlight fields that came from OCR.
- Buttons:
  - **Save Draft**
  - **Submit for Approval**

States:
- Display inline errors for missing fields.
- Show converted amount and base currency once valid amount/currency entered.

#### 6.3.3 My Claims

Table columns:
- Claim ID (or short reference).
- Submission date.
- Category.
- Original amount + currency.
- Converted amount + base currency.
- Current status.
- Last approver / Last action (optional).
- Actions:
  - View Detail.
  - Edit (only allowed in `DRAFT` or `REJECTED` states, before resubmission constraints).

Filters:
- Status tabs: All, Draft, In Review, Approved, Rejected.
- Simple date range filter.

### 6.4 Approver View

#### 6.4.1 Approvals Inbox

Table columns:
- Claim ID.
- Employee name.
- Department.
- Category.
- Amount (both currencies).
- Submitted date.
- Current step / step name.
- Action: "Review".

Filters:
- Default: status = pending for current user.
- Optional: filter by category or department.

#### 6.4.2 Claim Detail (Approver)

Sections:
- Header:
  - Claim ID, employee, department, status, created/submitted dates.
- Monetary block:
  - Amount in original currency.
  - Converted amount with base currency.
  - Exchange rate info (e.g., "1 USD = 83 INR on 2026-03-29").
- Receipt:
  - Thumbnail or embedded viewer.
- OCR section:
  - Merchant, date, total, maybe items.
- Timeline:
  - ApprovalActionLog events.

Actions:
- Approve (button).
- Reject (button with required comment modal).

UI must clearly indicate if this approval is part of a sequence or group (e.g., "Step 1 of 2: Manager Approval").

### 6.5 Admin View

#### 6.5.1 Admin Dashboard

Shows:
- At-a-glance statistics for:
  - Number of claims in review.
  - Approved this month.
  - Rejected this month.
- Recent high-value claims.

#### 6.5.2 User Management

Table:
- Email, name.
- Department.
- Role.
- Manager.
- Approver flag.
- Status (active/inactive).

Actions:
- Create user:
  - Email, name, role, department, manager, is_approver.
- Edit user.
- Deactivate user.

#### 6.5.3 Department Management

- List departments.
- Create/edit department (name, code).

#### 6.5.4 Category Management

- List categories.
- Add/edit category (name, code, description, active flag).
- Pre-seed defaults, but allow full CRUD.

#### 6.5.5 Approval Rule Management

Rule List:
- Rule name.
- Scope summary: amount range, categories, departments.
- Strategy summary: sequential or min-approvals.
- Active/inactive toggle.

Rule Detail (simple form-based UI, not drag-and-drop):
- General:
  - Name.
  - Description.
  - Active toggle.
  - Priority (number).
- Conditions:
  - Min amount (optional).
  - Max amount (optional).
  - Category (multi-select or single for V1).
  - Department (optional).
- Strategy:
  - Radio: Sequential / Min approvals.
  - If Min approvals:
    - Field: minimum approval percentage (0–100).
- Steps:
  - A vertical list of steps (for sequential).
  - For each step:
    - Step name.
    - Approver type (Manager / Specific User).
    - If Specific User: select user.
  - Allow add/remove steps.

---

## 7. API Design

### 7.1 Authentication

#### 7.1.1 POST `/auth/signup`

Request body:
- `company_name`
- `country_code`
- `admin_first_name`
- `admin_last_name`
- `email`
- `password`

Response:
- `access_token`
- `refresh_token`
- `user` object
- `company` object

#### 7.1.2 POST `/auth/login`

Request body:
- `email`
- `password`

Response:
- `access_token`
- `refresh_token`
- `user` object
- `company` object

#### 7.1.3 POST `/auth/refresh`

Uses refresh token to issue new access token.

### 7.2 Users

- GET `/users/me` – current user profile.
- GET `/users/` – (Admin only) list company users with filters.
- POST `/users/` – (Admin) create user.
- PATCH `/users/{id}` – updates user details, role, department, manager, is_approver.

### 7.3 Departments

- GET `/departments/`
- POST `/departments/`
- PATCH `/departments/{id}`

### 7.4 Categories

- GET `/categories/`
- POST `/categories/`
- PATCH `/categories/{id}`

### 7.5 Receipts & OCR

- POST `/receipts/`
  - Form-data upload: `file`.
  - Response: `receipt_file_id`, `ocr_extraction` (if sync).
- GET `/receipts/{id}` – metadata or file download token.

If async OCR:
- GET `/receipts/{id}/ocr` – returns `OCRExtraction` once complete.

### 7.6 Claims

- POST `/claims/` – create new claim, either draft or submitted.
  - Request body:
    - `title`
    - `description`
    - `category_id`
    - `receipt_file_id`
    - `original_currency`
    - `original_amount`
    - `expense_date`
    - `status` (`DRAFT` or `SUBMITTED`)
- GET `/claims/` – list claims for current user or all for admin with role-based filtering and query params (status, date range, category).
- GET `/claims/{id}` – detail view with current approval tasks, actions log, receipt & OCR.
- PATCH `/claims/{id}` – update claim fields (allowed transitions based on status).
- POST `/claims/{id}/submit` – transition from Draft → Submitted (and trigger approval engine).
- POST `/claims/{id}/resubmit` – for rejected claims.

### 7.7 Approval Rules

- GET `/approval_rules/`
- POST `/approval_rules/`
- GET `/approval_rules/{id}`
- PATCH `/approval_rules/{id}`
- DELETE (soft) `/approval_rules/{id}`

### 7.8 Approvals

- GET `/approvals/tasks`
  - Query params:
    - `status` (default `PENDING`)
    - Pagination params.
- POST `/approvals/tasks/{id}/approve`
  - Request body: optional `comment`.
- POST `/approvals/tasks/{id}/reject`
  - Request body: required `comment`.

### 7.9 Exchange Rates

- GET `/exchange_rates/preview`
  - Query: `base_currency`, `foreign_currency`, `amount`.
  - Response: `converted_amount`, `rate`, `provider`.

### 7.10 Audit

- GET `/audit/logs`
  - Admin-only listing with filters: entity type, date, user.

---

## 8. Validation & Business Rules

### 8.1 Validation

- Monetary fields:
  - `original_amount` > 0.
- Date:
  - `expense_date` cannot be in the far future (e.g., > 30 days ahead).
- Claim transitions:
  - Only `DRAFT` → `SUBMITTED`.
  - Only `REJECTED` → `IN_REVIEW` via resubmission.
  - Employees cannot edit `APPROVED` or `IN_REVIEW` claims except as allowed by admin overrides.
- Rules:
  - For each approval rule, `min_amount <= max_amount` (if both set).
  - `priority` non-negative int; collisions resolved by earliest creation time.

### 8.2 Business Constraints

- If an employee has no manager and a rule step requires `MANAGER`, fallback behavior:
  - Configurable default: company admin, or an error requiring admin to set a manager.
- If no rule exists and employee also has no manager, block submission with meaningful error for V1.

---

## 9. Non-Functional Requirements

### 9.1 Performance

- Target under hackathon constraints:
  - API response time < 500ms for main endpoints under typical demo load.
- Pagination on all list endpoints to prevent large responses:
  - default `page_size = 20`.

### 9.2 Security

- JWT-based access control, tokens signed and expired appropriately (e.g., 15–30 minute access token).
- Passwords stored hashed with bcrypt or similar.
- Role-based route protection enforced on backend; frontend also hides inaccessible menus but never relies on UI checks only.

### 9.3 Reliability

- DB-level constraints for FKs and uniqueness.
- Basic error handling and user-friendly error messages on UI.

---

## 10. Implementation Plan (High-Level)

Suggested order for a time-bound hackathon:

1. **Auth & Company bootstrap**
   - Implement signup/login, JWT, and sidebar layout.
2. **Core models & migrations**
   - Company, User, Department, Category, Claim, ReceiptFile, OCRExtraction, ApprovalRule/Step, ApprovalTask, ExchangeRateSnapshot.
3. **Employee flows**
   - Submit expense, draft and submit, My Claims.
4. **Approver flows**
   - Approvals inbox, approve/reject actions.
5. **Admin basic**
   - Manage users, departments, categories.
6. **Approval rules**
   - Simple rule builder; integrate rule engine.
7. **OCR integration**
   - Basic extraction and pre-fill.
8. **Currency conversion**
   - Simple conversion service with snapshot storing.
9. **Polish**
   - Status timelines, filtering, validations, audit logs.

---

## 11. Demo Scenario (For Hackathon)

1. **Admin Signup**
   - Create company “Acme Corp” with country “IN” → base currency “INR”.
2. **Admin creates users**
   - Employee “Alice”, Approver “Bob” as Alice’s manager.
3. **Admin creates rule**
   - Rule for Travel expenses over 100 USD equivalent → sequential approvals: Bob (Manager) → Finance approver.
4. **Employee submits expense**
   - Uploads USD travel receipt.
   - OCR pre-fills amount/date.
   - System converts USD→INR and routes as per rule.
5. **Bob approves**
   - Approves from Approvals Inbox.
6. **Finance approves**
   - Final approval; status moves to APPROVED.
7. Optional: show rejected + resubmission flow and simple admin audit log.

This scenario directly demonstrates that the system satisfies the hackathon problem statement: threshold-based approvals, multi-level routing, flexible rules, auto company currency, OCR, and clear status tracking.