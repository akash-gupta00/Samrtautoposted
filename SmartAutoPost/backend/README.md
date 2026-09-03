# SmartAutoPost – Full Source Package

This package combines the supplied FastAPI backend with a complete Jinja2 SaaS frontend.

## Quick start (Windows PowerShell)

```powershell
cd SmartAutoPost\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set DATABASE_URL + secrets
alembic upgrade head
uvicorn app.main:app --reload
```

Open:
- UI: http://127.0.0.1:8000/login
- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/v1/health

## Notes
`venv`, `.env`, cache files, and secrets are intentionally excluded. See `docs/PROJECT_AUDIT.md` and `docs/API_INVENTORY.md`.
