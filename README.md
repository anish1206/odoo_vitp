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
<img width="790" height="855" alt="Screenshot 2026-03-29 165208" src="https://github.com/user-attachments/assets/60eeb6ed-345c-4bb4-8c41-e5904b3a3c24" />
<img width="1004" height="678" alt="Screenshot 2026-03-29 165148" src="https://github.com/user-attachments/assets/3a7ae367-d158-4e11-91fe-b9911383a3cf" />
<img width="1868" height="720" alt="Screenshot 2026-03-29 174519" src="https://github.com/user-attachments/assets/957f77dd-2600-497d-99b1-c36176b1abdb" />
<img width="1884" height="725" alt="Screenshot 2026-03-29 174541" src="https://github.com/user-attachments/assets/32218341-459d-40d6-b8eb-ac81a882dfbd" />
<img width="1536" height="720" alt="Screenshot 2026-03-29 174609" src="https://github.com/user-attachments/assets/4d57c3e8-43da-451b-88f2-e8702b9bb9ea" />
<img width="1866" height="852" alt="Screenshot 2026-03-29 174802" src="https://github.com/user-attachments/assets/8c8da8fc-643a-40f0-876f-5839aa0d3ced" />
<img width="1849" height="781" alt="Screenshot 2026-03-29 174852" src="https://github.com/user-attachments/assets/2e0449ef-3b22-4f95-a457-6d8004c33a56" />
<img width="1535" height="662" alt="Screenshot 2026-03-29 175016" src="https://github.com/user-attachments/assets/a83ccab7-5afa-44e0-a78c-0a140f9992a0" />


## Repository Structure

- backend: FastAPI application, models, routers, services, migrations
- frontend: React + TypeScript application
- test: API and unit tests
- other: PRD and supporting assets
