# Recruiter AI Platform - Local Demo Run Script

Write-Host "Starting Recruiter AI Platform..."

# Ensure we are in root
$ROOT = Get-Location

# 1. Setup Backend
if (-not (Test-Path ".env")) {
    Copy-Item "env.example" ".env"
}

# Fix SECRET_KEY to be stable
$env_content = Get-Content ".env"
if ($env_content -notmatch "SECRET_KEY=") {
    Add-Content ".env" "SECRET_KEY=demo_secret_key_12345"
}

# Ensure DB
if (-not (Test-Path "recruiter_ai.db")) {
    python -c "from app.database import create_tables; create_tables()"
}

Write-Host "Server starting at http://localhost:8000/ui" -ForegroundColor Green
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
