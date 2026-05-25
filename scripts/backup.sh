#!/usr/bin/env bash
# =============================================================================
# MediCode — Database Backup Script (Bash)
# =============================================================================
# Usage:
#   bash scripts/backup.sh                    # backup to default location
#   bash scripts/backup.sh -o /path/backups   # backup to custom directory
#   bash scripts/backup.sh -r                 # rotate old backups (keep 14 days)
#
# Backs up SQLite database + exported JSON data.
# For PostgreSQL, uses pg_dump inside the container.
# =============================================================================

set -euo pipefail

# ---- Config ----
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"
DB_FILE="${PROJECT_ROOT}/data/medicode.db"   # SQLite default
RETENTION_DAYS=14
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# ---- Colors ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# ---- Parse Args ----
while getopts "o:r" opt; do
    case $opt in
        o) BACKUP_DIR="$OPTARG" ;;
        r) ROTATE_ONLY=true ;;
        *) echo "Usage: $0 [-o output_dir] [-r rotate-only]" && exit 1 ;;
    esac
done

# ---- Setup ----
mkdir -p "${BACKUP_DIR}"
BACKUP_NAME="medicode_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "${BACKUP_PATH}"

echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo -e "${CYAN}  MediCode Database Backup${NC}"
echo -e "${CYAN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}[backup]${NC} Timestamp: ${TIMESTAMP}"
echo -e "${GREEN}[backup]${NC} Output:    ${BACKUP_PATH}"

# ---- Detect Database Type ----
# Source .env if it exists
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a; source "${PROJECT_ROOT}/.env"; set +a
fi

DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./data/medicode.db}"
echo -e "${GREEN}[backup]${NC} Database:  ${DATABASE_URL}"

# ---- SQLite Backup ----
if [[ "${DATABASE_URL}" == sqlite* ]]; then
    echo -e "${YELLOW}[backup]${NC} Backing up SQLite database..."

    # Extract the file path from the URL
    DB_PATH="${DATABASE_URL#sqlite*:///}"
    DB_PATH="${PROJECT_ROOT}/$(dirname "${DB_PATH}")/$(basename "${DB_PATH}")"

    # If running in Docker, copy from container
    if docker compose ps --format json 2>/dev/null | grep -q "medicode-backend"; then
        echo -e "${YELLOW}[backup]${NC} Running in Docker context — copying from backend container..."
        docker compose cp backend:/app/data/medicode.db "${BACKUP_PATH}/medicode.db" 2>/dev/null || {
            echo -e "${RED}[backup]${NC} Failed to copy from container; trying local file..."
            if [ -f "${DB_PATH}" ]; then
                cp "${DB_PATH}" "${BACKUP_PATH}/medicode.db"
            fi
        }
    elif [ -f "${DB_PATH}" ]; then
        echo -e "${YELLOW}[backup]${NC} Copying local SQLite file..."
        cp "${DB_PATH}" "${BACKUP_PATH}/medicode.db"
    else
        echo -e "${RED}[backup]${NC} SQLite database not found at: ${DB_PATH}"
        echo -e "${YELLOW}[backup]${NC} Trying Docker volume..."
        docker compose cp backend:/app/data/medicode.db "${BACKUP_PATH}/medicode.db" 2>/dev/null || {
            echo -e "${RED}[backup]${NC} Could not locate database file."
        }
    fi

    # Verify SQLite backup
    if [ -f "${BACKUP_PATH}/medicode.db" ]; then
        SIZE=$(stat -f%z "${BACKUP_PATH}/medicode.db" 2>/dev/null || stat -c%s "${BACKUP_PATH}/medicode.db" 2>/dev/null || echo "0")
        echo -e "${GREEN}[backup]${NC} SQLite backup: ${BACKUP_PATH}/medicode.db (${SIZE} bytes)"

        # Dump tables to JSON for readable backup
        echo -e "${YELLOW}[backup]${NC} Exporting tables to JSON..."
        python3 -c "
import sqlite3, json, os, datetime
db = sqlite3.connect('${BACKUP_PATH}/medicode.db')
cursor = db.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'alembic_%'\")
tables = [row[0] for row in cursor.fetchall()]
export = {'exported_at': '${TIMESTAMP}', 'tables': {}}
for table in tables:
    try:
        cursor.execute(f'SELECT * FROM \"{table}\" LIMIT 100000')
        cols = [desc[0] for desc in cursor.description]
        rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
        export['tables'][table] = {'count': len(rows), 'data': rows}
    except Exception as e:
        print(f'Warning: Could not export {table}: {e}', flush=True)
with open('${BACKUP_PATH}/data_export.json', 'w', encoding='utf-8') as f:
    json.dump(export, f, ensure_ascii=False, indent=2, default=str)
db.close()
" 2>/dev/null && echo -e "${GREEN}[backup]${NC} JSON export: ${BACKUP_PATH}/data_export.json" || \
            echo -e "${YELLOW}[backup]${NC} JSON export skipped (Python unavailable)"
    fi

# ---- PostgreSQL Backup ----
elif [[ "${DATABASE_URL}" == postgresql* ]]; then
    echo -e "${YELLOW}[backup]${NC} Backing up PostgreSQL database..."
    docker compose exec -T postgres pg_dump -U medicode medicode > "${BACKUP_PATH}/medicode.sql" 2>/dev/null || {
        echo -e "${RED}[backup]${NC} pg_dump failed. Is the postgres container running?"
    }
    echo -e "${GREEN}[backup]${NC} PostgreSQL backup: ${BACKUP_PATH}/medicode.sql"
fi

# ---- Compress ----
echo -e "${YELLOW}[backup]${NC} Compressing backup..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}" 2>/dev/null || \
    zip -r "${BACKUP_NAME}.zip" "${BACKUP_NAME}" > /dev/null
rm -rf "${BACKUP_PATH}"

ARCHIVE_PATH=""
if [ -f "${BACKUP_NAME}.tar.gz" ]; then
    ARCHIVE_PATH="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
elif [ -f "${BACKUP_NAME}.zip" ]; then
    ARCHIVE_PATH="${BACKUP_DIR}/${BACKUP_NAME}.zip"
fi

if [ -n "${ARCHIVE_PATH}" ]; then
    SIZE=$(stat -f%z "${ARCHIVE_PATH}" 2>/dev/null || stat -c%s "${ARCHIVE_PATH}" 2>/dev/null || echo "0")
    echo -e "${GREEN}[backup]${NC} Archive: ${ARCHIVE_PATH} (${SIZE} bytes)"
fi

# ---- Rotate Old Backups ----
echo -e "${YELLOW}[backup]${NC} Rotating backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "medicode_backup_*" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || \
    powershell -Command "Get-ChildItem '${BACKUP_DIR}' -Filter 'medicode_backup_*' | Where-Object { \$_.LastWriteTime -lt (Get-Date).AddDays(-${RETENTION_DAYS}) } | Remove-Item -Force" 2>/dev/null

# ---- Summary ----
echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Backup Complete!${NC}"
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "Timestamp: ${TIMESTAMP}"
echo -e "Retention: ${RETENTION_DAYS} days"
echo -e "Existing backups: $(find "${BACKUP_DIR}" -name "medicode_backup_*" | wc -l) files"
