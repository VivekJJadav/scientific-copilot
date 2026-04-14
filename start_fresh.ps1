<#
.SYNOPSIS
    Fresh-start script for Scientific Copilot.
    Drops all database tables (keeps the Ollama model intact),
    re-applies migrations, and launches backend + frontend.

.USAGE
    .\start_fresh.ps1            # full wipe + start
    .\start_fresh.ps1 -SkipDb    # skip DB reset, just start services
#>

param(
    [switch]$SkipDb
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition
$UI   = Join-Path $ROOT "scientific-copilot-ui"

# ---- Helpers ----
function Write-Step  { param($msg) Write-Host "`n> $msg" -ForegroundColor Cyan }
function Write-Ok    { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "  [ERR] $msg" -ForegroundColor Red }

# ---- 0. Pre-flight checks ----
Write-Step "Pre-flight checks"

$pg = docker ps --filter "ancestor=pgvector/pgvector:pg16" --format "{{.ID}}" 2>$null
if (-not $pg) {
    Write-Warn "PostgreSQL container not running - starting docker compose..."
    docker compose -f "$ROOT\docker-compose.yml" up -d postgres
    Start-Sleep -Seconds 5
    $pg = docker ps --filter "ancestor=pgvector/pgvector:pg16" --format "{{.ID}}" 2>$null
    if (-not $pg) {
        Write-Err "Failed to start PostgreSQL container"; exit 1
    }
    Write-Ok "PostgreSQL container started"
} else {
    Write-Ok "PostgreSQL container running ($pg)"
}

# ---- 1. Reset database (tables only, Ollama model untouched) ----
if (-not $SkipDb) {
    Write-Step "Dropping all tables in 'scientific_copilot' database..."

    # Write a temp SQL file to avoid PowerShell escaping issues
    $sqlFile = Join-Path $ROOT "scratch_drop_tables.sql"
    @'
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
CREATE EXTENSION IF NOT EXISTS vector;
'@ | Set-Content -Path $sqlFile -Encoding UTF8

    # Pipe the SQL file into psql inside the container
    Get-Content $sqlFile | docker exec -i $pg psql -U postgres -d scientific_copilot
    if ($LASTEXITCODE -ne 0) {
        Remove-Item $sqlFile -ErrorAction SilentlyContinue
        Write-Err "Failed to drop tables"; exit 1
    }
    Remove-Item $sqlFile -ErrorAction SilentlyContinue
    Write-Ok "All tables dropped (Ollama model is untouched)"

    # ---- 2. Run Alembic migrations ----
    Write-Step "Running Alembic migrations..."
    Push-Location $ROOT
    uv run alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Alembic migration failed"; Pop-Location; exit 1
    }
    Pop-Location
    Write-Ok "Migrations applied"
} else {
    Write-Warn "Skipping DB reset (-SkipDb flag)"
}

# ---- 3. Start backend (uvicorn) ----
Write-Step "Starting backend (uvicorn)..."
$backendJob = Start-Job -Name "backend" -ScriptBlock {
    Set-Location $using:ROOT
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}
Write-Ok "Backend starting in background job [backend]"

# ---- 4. Start frontend (next dev) ----
Write-Step "Starting frontend (next dev)..."
$frontendJob = Start-Job -Name "frontend" -ScriptBlock {
    Set-Location $using:UI
    npm run dev
}
Write-Ok "Frontend starting in background job [frontend]"

# ---- 5. Stream logs ----
Write-Host ""
Write-Host "=====================================================" -ForegroundColor DarkGray
Write-Host "  Backend  -> http://localhost:8000"               -ForegroundColor White
Write-Host "  Frontend -> http://localhost:3000"               -ForegroundColor White
Write-Host "  Ollama   -> http://localhost:11434  (untouched)" -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor DarkGray
Write-Host "  Press Ctrl+C to stop all services."              -ForegroundColor DarkGray
Write-Host ""

try {
    while ($true) {
        Receive-Job -Job $backendJob  -ErrorAction SilentlyContinue | Write-Host
        Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue | Write-Host
        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host "`nShutting down..." -ForegroundColor Yellow
    Stop-Job    -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job  -Job $backendJob, $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Ok "All services stopped."
}
