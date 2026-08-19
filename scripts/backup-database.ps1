[CmdletBinding()]
param(
    [string]$DatabasePath = $env:DATABASE_PATH,
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$BackupDirectory = $env:BACKUP_DIR,
    [int]$RetentionDays = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($RetentionDays -le 0) {
    $RetentionDays = if ($env:BACKUP_RETENTION_DAYS) { [int]$env:BACKUP_RETENTION_DAYS } else { 14 }
}
if ($RetentionDays -lt 1) { throw "RetentionDays must be at least 1." }

if ([string]::IsNullOrWhiteSpace($BackupDirectory)) {
    if ([string]::IsNullOrWhiteSpace($DatabasePath)) { throw "Set BackupDirectory when backing up PostgreSQL." }
    $BackupDirectory = Join-Path (Split-Path -Parent $DatabasePath) "backups"
}
New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

if (-not [string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
        throw "pg_dump was not found. Install PostgreSQL client tools before backing up DATABASE_URL."
    }
    $backupPath = Join-Path $BackupDirectory "ai-resume-$timestamp.dump"
    & pg_dump "--dbname=$DatabaseUrl" "--format=custom" "--file=$backupPath"
    if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE." }
} else {
    if ([string]::IsNullOrWhiteSpace($DatabasePath) -or -not (Test-Path -LiteralPath $DatabasePath -PathType Leaf)) {
        throw "DatabasePath must point to an existing SQLite database."
    }
    $snapshotPath = Join-Path $BackupDirectory "ai-resume-$timestamp.db"
    $backupPath = Join-Path $BackupDirectory "ai-resume-$timestamp.zip"
    $backupCode = "import sqlite3, sys; source = sqlite3.connect(sys.argv[1]); target = sqlite3.connect(sys.argv[2]); source.backup(target); target.close(); source.close()"
    & python -c $backupCode $DatabasePath $snapshotPath
    if ($LASTEXITCODE -ne 0) { throw "SQLite backup snapshot failed with exit code $LASTEXITCODE." }
    try {
        Compress-Archive -LiteralPath $snapshotPath -DestinationPath $backupPath -CompressionLevel Optimal -Force
    } finally {
        Remove-Item -LiteralPath $snapshotPath -Force -ErrorAction SilentlyContinue
    }
}

$cutoff = (Get-Date).ToUniversalTime().AddDays(-$RetentionDays)
Get-ChildItem -LiteralPath $BackupDirectory -File -Filter "ai-resume-*" |
    Where-Object { $_.LastWriteTimeUtc -lt $cutoff } |
    Remove-Item -Force

# TODO: Register this script with Windows Task Scheduler only after a restore drill succeeds.
Write-Output $backupPath
