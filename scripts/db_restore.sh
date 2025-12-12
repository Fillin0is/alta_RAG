#!/bin/bash

# Database restore script for RAG System
# Usage: ./scripts/db_restore.sh <backup_file>

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Available backups:"
    ls -lh backups/rag_backup_*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file ${BACKUP_FILE} not found"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

DB_NAME=${DB_NAME:-rag_system_local}
DB_USER=${DB_USER:-postgres}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

echo "Warning: This will restore database ${DB_NAME} from ${BACKUP_FILE}"
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Decompress if needed
if [[ ${BACKUP_FILE} == *.gz ]]; then
    echo "Decompressing backup..."
    TEMP_FILE="${BACKUP_FILE%.gz}"
    gunzip -c ${BACKUP_FILE} > ${TEMP_FILE}
    BACKUP_TO_RESTORE=${TEMP_FILE}
else
    BACKUP_TO_RESTORE=${BACKUP_FILE}
fi

echo "Restoring database ${DB_NAME}..."
PGPASSWORD=${DB_PASSWORD} pg_restore -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -c -F c ${BACKUP_TO_RESTORE}

# Clean up temp file if we decompressed
if [[ ${BACKUP_FILE} == *.gz ]]; then
    rm ${TEMP_FILE}
fi

echo "Restore completed successfully!"
