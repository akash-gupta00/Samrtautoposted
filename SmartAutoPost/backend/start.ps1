if (-not (Test-Path "venv")) { python -m venv venv }
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "Created .env — edit it before continuing." }
uvicorn app.main:app --reload
