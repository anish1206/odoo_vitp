# Reimbursement Management System

Hackathon-ready full-stack expense reimbursement platform with OCR-assisted claim capture, configurable approval routing, manager fallback logic, and multi-currency conversion.

## What Is Addressed

All major PRD goals are implemented in the current codebase.

- Company bootstrap on first signup with admin creation and base currency setup.
- JWT auth flow: signup, login, refresh, and current user profile endpoint.
- Employee claim lifecycle: draft, edit, submit, filter, and detail timeline.
- Receipt upload and OCR extraction context in claim and approval views.
- Multi-level approval workflow with approval inbox, approve/reject actions, and comments.
- Manager chain fallback when configured rule approvers are unavailable.
- Admin management modules: company settings, users, departments, categories, approval rules, and all company claims.
- Live exchange-rate conversion with fallback behavior for resilience.
- Claim and approval audit timeline/log visibility in UI detail panels.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, SQLite/PostgreSQL-compatible modeling
- Frontend: React, TypeScript, Vite, React Router, Axios
- OCR: Gemini integration with local fallback behavior
- Auth: JWT access + refresh token pattern

## Implemented API Areas

- Auth: /auth/signup, /auth/login, /auth/refresh
- Users: /users/me, admin user CRUD endpoints
- Claims: my claims, company claims, claim detail, draft update, submit
- Approvals: task inbox, task detail, approve, reject
- Admin masters: departments, categories, approval rules
- Receipts: upload and OCR retrieval
- Exchange rates: conversion preview endpoint
- Health: /health

Interactive API docs are available at:

- http://localhost:8000/docs

## Frontend Coverage

- Auth pages: Login and Signup
- Employee pages: Dashboard, Submit Expense, My Claims
- Approver page: Approvals Inbox with claim context and timeline
- Admin pages: Company Settings, All Claims, Users, Departments, Categories, Approval Rules

## Local Setup

### 1. Backend

From repository root:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
copy backend\.env.example backend\.env
```

Run migrations (recommended):

```bash
cd backend
alembic upgrade head
```

Start API:

```bash
# from backend directory
uvicorn app.main:app --reload

# or from repo root
uvicorn app.main:app --reload --app-dir backend
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL:

- http://localhost:5173

## Environment Configuration

Base backend env template is in backend/.env.example.

Key runtime variables:

```dotenv
RMS_UPLOADS_DIR=./uploads
RMS_CURRENCY_PROVIDER=live-with-fallback
RMS_CURRENCY_API_URL=https://api.exchangerate.host/latest
RMS_CURRENCY_TIMEOUT_SECONDS=6
RMS_GEMINI_API_KEY=
RMS_GEMINI_MODEL=gemini-2.0-flash
RMS_GEMINI_OCR_TIMEOUT_SECONDS=20
```

Notes:

- Leave RMS_GEMINI_API_KEY empty to rely on fallback behavior.
- live-with-fallback currency provider keeps conversion usable during provider/API issues.

## Validation Status

- Frontend production build command is available and passing in current workflow: npm run build
- Backend test suite available from repository root: pytest

## Screenshots

Add your demo screenshots in this section before final submission.

### Authentication

![alt text](<Screenshot 2026-03-29 165148.png>)
![alt text](<Screenshot 2026-03-29 165208.png>)

### Employee Flow

![alt text](image.png)
![alt text](image-1.png)
![alt text](image-2.png)

### Approver Flow

![alt text](image-3.png)

### Admin Flow

![alt text](image-4.png)
![alt text](image-5.png)

## Repository Structure

- backend: FastAPI application, models, routers, services, migrations
- frontend: React + TypeScript application
- test: API and unit tests
- other: PRD and supporting assets
