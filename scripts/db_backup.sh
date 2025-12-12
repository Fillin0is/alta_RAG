#!/bin/bash

# Database backup script for RAG System
# Usage: ./scripts/db_backup.sh

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

DB_NAME=${DB_NAME:-rag_system_local}
DB_USER=${DB_USER:-postgres}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/rag_backup_${TIMESTAMP}.sql"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

echo "Creating backup of database ${DB_NAME}..."
PGPASSWORD=${DB_PASSWORD} pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -F c -f ${BACKUP_FILE}

echo "Backup created: ${BACKUP_FILE}"

# Compress backup
gzip ${BACKUP_FILE}
echo "Backup compressed: ${BACKUP_FILE}.gz"

# Clean up old backups (keep last 7 days)
find ${BACKUP_DIR} -name "rag_backup_*.sql.gz" -mtime +7 -delete
echo "Old backups cleaned up (kept last 7 days)"

echo "Backup completed successfully!"
