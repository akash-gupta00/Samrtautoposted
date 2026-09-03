# SmartAutoPost – Full Frontend + Backend

This package preserves the FastAPI backend and adds a multi-page Jinja2 SaaS frontend.

## Setup
1. Copy `.env.example` to `.env` and fill database/API credentials.
2. Run `run.bat` or install requirements and execute `uvicorn app.main:app --reload`.
3. Open http://127.0.0.1:8000/login

## UI routes
/login, /register, /dashboard, /create-post, /posts, /ai-content, /calendar, /analytics, /social-accounts, /media-library, /competitors, /clients, /organizations, /roles, /billing, /notifications, /profile, /settings, /audit-logs.

The frontend calls the existing `/api/v1` APIs. External integrations require valid credentials.
