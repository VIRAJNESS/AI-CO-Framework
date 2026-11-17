<#
.SYNOPSIS
  Docker-free local startup (fallback mode) for AI Coach Mastery.

  Starts all three tiers without containers:
    core-api  : Spring Boot 'local' profile (H2 file DB, showcase auto-seeds)
    ai-engine : uvicorn in a .venv (mock LLM, local filesystem storage)
    frontend  : ng serve with proxy.local.json (localhost targets)

  Prereqs: JDK 21+, Python 3.11+, Node 20+. Maven is auto-downloaded if absent.
  Usage:   .\start-local.ps1          (from the repo root)
#>

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

Write-Host "== AI Coach Mastery — Docker-free local mode ==" -ForegroundColor Cyan

# --- Dependency checks ---------------------------------------------------------
foreach ($tool in @('java', 'python', 'node', 'npm')) {
  if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
    Write-Error "Required tool '$tool' not found on PATH. Install it and retry."
  }
}

# --- Maven (download portable copy if not installed) -----------------------------
$mvn = (Get-Command mvn -ErrorAction SilentlyContinue).Source
if (-not $mvn) {
  $mvnHome = Join-Path $env:TEMP 'apache-maven-3.9.9'
  $mvn = Join-Path $mvnHome 'bin\mvn.cmd'
  if (-not (Test-Path $mvn)) {
    Write-Host "Maven not found — downloading portable Maven 3.9.9..." -ForegroundColor Yellow
    $zip = Join-Path $env:TEMP 'maven.zip'
    Invoke-WebRequest -Uri 'https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.zip' -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $env:TEMP -Force
  }
}
Write-Host "Maven: $mvn"

# --- ai-engine venv ---------------------------------------------------------------
$venv = Join-Path $root 'ai-engine\.venv'
$venvPy = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $venvPy)) {
  Write-Host "Creating ai-engine venv + installing dependencies (one-time)..." -ForegroundColor Yellow
  python -m venv $venv
  & $venvPy -m pip -q install --upgrade pip
  # Unpinned: resolves wheels for whatever modern Python is installed.
  & $venvPy -m pip -q install fastapi "uvicorn[standard]" "pydantic>=2" pydantic-settings `
      httpx numpy scipy statsmodels python-pptx python-docx reportlab matplotlib
}

# --- frontend node_modules ----------------------------------------------------------
if (-not (Test-Path (Join-Path $root 'frontend\node_modules'))) {
  Write-Host "Installing frontend dependencies (one-time)..." -ForegroundColor Yellow
  Push-Location (Join-Path $root 'frontend')
  npm install --no-audit --no-fund
  Pop-Location
}

# --- Launch tiers in separate windows -------------------------------------------------
Write-Host "`nStarting ai-engine on :8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @('-NoExit', '-Command',
  "Set-Location '$root\ai-engine'; " +
  "`$env:LLM_PROVIDER='mock'; `$env:STORAGE_PROVIDER='local'; " +
  "`$env:LOCAL_STORAGE_PATH='$root\ai-engine\artifacts'; " +
  "& '$venvPy' -m uvicorn app.main:app --host 0.0.0.0 --port 8000")

Write-Host "Starting core-api on :8080 (local profile, H2) ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @('-NoExit', '-Command',
  "Set-Location '$root\core-api'; " +
  "& '$mvn' -q spring-boot:run '-Dspring-boot.run.profiles=local'")

Write-Host "Starting frontend on :4200 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @('-NoExit', '-Command',
  "Set-Location '$root\frontend'; " +
  "npx ng serve --proxy-config proxy.local.json --open")

Write-Host @"

All tiers launching in separate windows.
  Frontend : http://localhost:4200
  Core API : http://localhost:8080/swagger-ui.html
  AI Engine: http://localhost:8000/docs

First core-api start auto-seeds the 4 showcase clients (H2 file: core-api/.localdb).
Smoke-test once healthy:  python scripts/smoke_test.py
"@ -ForegroundColor Cyan
