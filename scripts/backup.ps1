# =============================================================================
# MediCode — Database Backup Script (PowerShell / Windows)
# =============================================================================
# Usage:
#   .\scripts\backup.ps1                    # backup to default location
#   .\scripts\backup.ps1 -OutputDir D:\backups  # backup to custom directory
#   .\scripts\backup.ps1 -RotateOnly        # rotate old backups only
# =============================================================================

param(
    [string]$OutputDir = "",
    [switch]$RotateOnly
)

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

$BACKUP_DIR = if ($OutputDir) { $OutputDir } else { Join-Path $PROJECT_ROOT "backups" }
$RETENTION_DAYS = 14
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_NAME = "medicode_backup_$TIMESTAMP"
$BACKUP_PATH = Join-Path $BACKUP_DIR $BACKUP_NAME

# Ensure backup directory exists
New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null

Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  MediCode Database Backup" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "[backup] Timestamp: $TIMESTAMP" -ForegroundColor Green
Write-Host "[backup] Output:    $BACKUP_PATH" -ForegroundColor Green

# Rotate old backups
if ($RotateOnly) {
    Write-Host "[backup] Rotating backups older than $RETENTION_DAYS days..." -ForegroundColor Yellow
    Get-ChildItem $BACKUP_DIR -Filter "medicode_backup_*" |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RETENTION_DAYS) } |
        Remove-Item -Force
    Write-Host "[backup] Rotation complete." -ForegroundColor Green
    return
}

# ---- SQLite Backup (local file) ----
$DB_FILE = Join-Path $PROJECT_ROOT "data" "medicode.db"

New-Item -ItemType Directory -Force -Path $BACKUP_PATH | Out-Null

if (Test-Path $DB_FILE) {
    Write-Host "[backup] Copying SQLite database..." -ForegroundColor Yellow
    Copy-Item $DB_FILE -Destination (Join-Path $BACKUP_PATH "medicode.db") -Force
    $size = (Get-Item (Join-Path $BACKUP_PATH "medicode.db")).Length
    Write-Host "[backup] SQLite backup: $BACKUP_PATH\medicode.db ($size bytes)" -ForegroundColor Green

    # Export to JSON using Python
    Write-Host "[backup] Exporting tables to JSON..." -ForegroundColor Yellow
    $pythonCode = @"
import sqlite3, json, os
db = sqlite3.connect(r'$($BACKUP_PATH)\medicode.db')
cursor = db.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'alembic_%'")
tables = [row[0] for row in cursor.fetchall()]
export = {'exported_at': '$TIMESTAMP', 'tables': {}}
for table in tables:
    try:
        cursor.execute(f'SELECT * FROM \"{table}\" LIMIT 100000')
        cols = [desc[0] for desc in cursor.description]
        rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
        export['tables'][table] = {'count': len(rows), 'data': rows}
    except Exception as e:
        print(f'Warning: Could not export {table}: {e}')
with open(r'$($BACKUP_PATH)\data_export.json', 'w', encoding='utf-8') as f:
    json.dump(export, f, ensure_ascii=False, indent=2, default=str)
db.close()
"@
    $pythonCode | python 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[backup] JSON export: $BACKUP_PATH\data_export.json" -ForegroundColor Green
    } else {
        Write-Host "[backup] JSON export skipped (Python error)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[backup] Local SQLite not found. Trying Docker volume..." -ForegroundColor Yellow
    docker compose cp backend:/app/data/medicode.db "$BACKUP_PATH/medicode.db" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[backup] SQLite backup from Docker: $BACKUP_PATH\medicode.db" -ForegroundColor Green
    } else {
        Write-Host "[backup] No SQLite database found. Skipping." -ForegroundColor Yellow
    }
}

# ---- Compress ----
Write-Host "[backup] Compressing backup..." -ForegroundColor Yellow
Set-Location $BACKUP_DIR
Compress-Archive -Path $BACKUP_NAME -DestinationPath "$BACKUP_NAME.zip" -Force
Remove-Item -Recurse -Force $BACKUP_PATH -ErrorAction SilentlyContinue

$zipFile = Join-Path $BACKUP_DIR "$BACKUP_NAME.zip"
if (Test-Path $zipFile) {
    $zipSize = (Get-Item $zipFile).Length
    Write-Host "[backup] Archive: $zipFile ($zipSize bytes)" -ForegroundColor Green
}

# ---- Rotate ----
Write-Host "[backup] Rotating backups older than $RETENTION_DAYS days..." -ForegroundColor Yellow
Get-ChildItem $BACKUP_DIR -Filter "medicode_backup_*" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RETENTION_DAYS) } |
    Remove-Item -Force

# ---- Summary ----
Write-Host ""
Write-Host "══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Backup Complete!" -ForegroundColor Green
Write-Host "══════════════════════════════════════════" -ForegroundColor Green
Write-Host "Timestamp: $TIMESTAMP"
Write-Host "Retention: $RETENTION_DAYS days"
$backupCount = (Get-ChildItem $BACKUP_DIR -Filter "medicode_backup_*" -ErrorAction SilentlyContinue).Count
Write-Host "Existing backups: $backupCount files"
