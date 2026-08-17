param(
  [int]$Port = 8004
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot "resume-backend"
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
  throw "Backend virtual environment is missing: $python"
}

$healthUrl = "http://127.0.0.1:$Port/health"
try {
  $health = (Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 2).Content | ConvertFrom-Json
  if ($health.data.capabilities -contains "job_plan" -and $health.data.capabilities -contains "job_match" -and $health.data.capabilities -contains "ai_setup") {
    Write-Output "Resume backend is current: $healthUrl"
    exit 0
  }
  throw "An outdated backend owns port $Port. Stop it, then run this script again."
} catch [System.Net.WebException] {
  # No listener yet: start the current worktree with reload so future source edits do not become stale.
}

Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "$Port" -WorkingDirectory $backendRoot -WindowStyle Hidden
for ($attempt = 0; $attempt -lt 20; $attempt += 1) {
  Start-Sleep -Milliseconds 500
  try {
    $health = (Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 2).Content | ConvertFrom-Json
    if ($health.data.capabilities -contains "job_plan" -and $health.data.capabilities -contains "job_match" -and $health.data.capabilities -contains "ai_setup") {
      Write-Output "Resume backend started: $healthUrl"
      exit 0
    }
  } catch [System.Net.WebException] {}
}
throw "Backend did not report the current capability set within 10 seconds."
