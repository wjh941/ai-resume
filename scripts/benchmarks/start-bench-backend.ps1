# Isolated benchmark backend launcher.
# Never touches the dev instance on port 8000 or the dev database.
# - Dedicated SQLite file: resume-backend/.bench/bench.db (-Fresh rebuilds it)
# - Skips .env (RESUME_SKIP_DOTENV=1); AI_* vars are passed through from .env, secrets are never printed
# - auth/AI rate limits are raised for this process only
param(
  [int]$Port = 8004,
  [switch]$Fresh
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backendRoot = Join-Path $projectRoot "resume-backend"
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Missing backend venv: $python" }

$benchDir = Join-Path $backendRoot ".bench"
New-Item -ItemType Directory -Force -Path $benchDir | Out-Null
if ($Fresh -and (Test-Path (Join-Path $benchDir "bench.db"))) {
  Remove-Item (Join-Path $benchDir "bench.db") -Force
}

if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
  throw "Port $Port is already in use. Stop the previous benchmark instance first."
}

# Pick AI config from the dev .env (never echoed); benchmark degrades gracefully when absent.
$ai = @{}
$envFile = Join-Path $backendRoot ".env"
if (Test-Path $envFile) {
  foreach ($line in Get-Content $envFile) {
    if ($line -match '^\s*(AI_PROVIDER|AI_BASE_URL|AI_API_KEY|AI_MODEL)\s*=\s*(.*)\s*$') {
      $ai[$Matches[1]] = $Matches[2]
    }
  }
}

$env:RESUME_SKIP_DOTENV = "1"
$env:APP_ENV = "development"
$env:APP_HOST = "127.0.0.1"
$env:APP_PORT = "$Port"
$env:DATABASE_PATH = (Join-Path $benchDir "bench.db")
$env:TEMP_FILE_PATH = (Join-Path $benchDir "temp")
$env:JWT_SECRET = "bench-only-secret-not-for-production-000000000000"
$env:AUTH_DEMO_MODE = "true"
$env:SMS_PROVIDER = "disabled"
$env:CORS_ORIGINS = ""
$env:AUTH_RATE_LIMIT_MAX_REQUESTS = "1000"
$env:AUTH_RATE_LIMIT_WINDOW_SECONDS = "60"
$env:AI_RATE_LIMIT_MAX_REQUESTS = "1000"
$env:AI_RATE_LIMIT_WINDOW_SECONDS = "60"
$env:WORKER_ENABLED = "false"
foreach ($k in $ai.Keys) { Set-Item -Path "env:$k" -Value $ai[$k] }

Write-Host "Starting isolated benchmark backend: http://127.0.0.1:$Port (db=$env:DATABASE_PATH)"
$proc = Start-Process -FilePath $python `
  -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "$Port", "--log-level", "warning" `
  -WorkingDirectory $backendRoot -PassThru -WindowStyle Hidden
Write-Host "uvicorn PID=$($proc.Id)"

for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Milliseconds 500
  try {
    $health = (Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$Port/health" -TimeoutSec 2).Content | ConvertFrom-Json
    if ($health.data.capabilities -contains "job_match") {
      Write-Host "Benchmark backend ready: http://127.0.0.1:$Port"
      $keyState = "not-configured"
      if ($ai["AI_API_KEY"]) { $keyState = "configured" }
      Write-Host ("AI config: provider={0} model={1} key={2}" -f $ai["AI_PROVIDER"], $ai["AI_MODEL"], $keyState)
      exit 0
    }
  } catch [System.Net.WebException] {}
}
throw "Benchmark backend did not become ready within 20 seconds."
