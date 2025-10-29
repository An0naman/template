#!/bin/bash
# Backup script for app instances
# Creates timestamped backup of all app data

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Template Framework Backup Script${NC}"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -d "data" ]; then
    echo -e "${RED}Error: data directory not found${NC}"
    echo "Please run this script from your app instance directory"
    exit 1
fi

# Load environment variables for app name
if [ -f ".env" ]; then
    source .env
fi

APP_NAME=${APP_NAME:-myapp}
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="backups"
BACKUP_FILE="${BACKUP_DIR}/${APP_NAME}-${TIMESTAMP}.tar.gz"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "App Name: ${APP_NAME}"
echo "Backup File: ${BACKUP_FILE}"
echo ""

# Calculate data directory size
DATA_SIZE=$(du -sh data/ | cut -f1)
echo "Data Directory Size: ${DATA_SIZE}"
echo ""

# Create backup
echo -e "${YELLOW}Creating backup...${NC}"
tar -czf "${BACKUP_FILE}" \
    data/ \
    docker-compose.yml \
    .env 2>/dev/null || true

# Verify backup
if [ -f "${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
    echo -e "${GREEN}✓ Backup created successfully${NC}"
    echo "Backup Size: ${BACKUP_SIZE}"
    echo "Location: ${BACKUP_FILE}"
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi

echo ""

# List recent backups
echo -e "${YELLOW}Recent backups:${NC}"
ls -lh "${BACKUP_DIR}" | tail -n 5
echo ""

# Cleanup old backups (keep last 10)
BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/*.tar.gz 2>/dev/null | wc -l)
if [ "${BACKUP_COUNT}" -gt 10 ]; then
    echo -e "${YELLOW}Cleaning up old backups (keeping last 10)...${NC}"
    ls -1t "${BACKUP_DIR}"/*.tar.gz | tail -n +11 | xargs rm -f
    echo -e "${GREEN}✓ Cleanup complete${NC}"
fi

echo ""
echo -e "${GREEN}=================================="
echo "✓ Backup completed successfully!"
echo "==================================${NC}"
echo ""
echo "To restore this backup:"
echo "  tar -xzf ${BACKUP_FILE}"
echo "  docker-compose restart"
echo ""
