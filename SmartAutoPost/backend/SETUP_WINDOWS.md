# Windows Setup

1. Install Python 3.12 or 3.13 and PostgreSQL.
2. Create a database named `smartautopost`.
3. Run:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```
