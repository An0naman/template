#!/bin/bash
# Run Database Migrations Script
# Executes all pending database migrations for an app instance

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Database Migration Runner${NC}"
echo "=========================="
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Please run this script from your app instance directory"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    source .env
else
    echo -e "${YELLOW}Warning: .env file not found, using defaults${NC}"
fi

APP_NAME=${APP_NAME:-myapp}

echo "App Name: ${APP_NAME}"
echo ""

# Check if container is running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}Error: Container is not running${NC}"
    echo "Start the container first with: docker-compose up -d"
    exit 1
fi

# Check if migrations directory exists in container
if ! docker-compose exec -T ${APP_NAME} test -d /app/migrations 2>/dev/null; then
    echo -e "${YELLOW}No migrations directory found in container${NC}"
    echo "This framework version may not have any migrations."
    exit 0
fi

# Create backup before running migrations
echo -e "${YELLOW}Step 1: Creating database backup...${NC}"
BACKUP_DIR="migration-backups"
mkdir -p ${BACKUP_DIR}
BACKUP_FILE="${BACKUP_DIR}/db-before-migration-$(date +%Y%m%d-%H%M%S).tar.gz"

if [ -d "data" ]; then
    tar -czf "${BACKUP_FILE}" data/ 2>/dev/null || echo "Backup created with warnings"
    echo -e "${GREEN}✓ Backup created: ${BACKUP_FILE}${NC}"
else
    echo -e "${YELLOW}⚠ No data directory found, skipping backup${NC}"
fi
echo ""

# Run migrations
echo -e "${YELLOW}Step 2: Running database migrations...${NC}"
echo ""

# Get list of all Python migration files
MIGRATIONS=$(docker-compose exec -T ${APP_NAME} sh -c "find /app/migrations -name '*.py' -not -path '*/\.*' -not -path '*/__pycache__/*' | sort" 2>/dev/null || echo "")

if [ -z "$MIGRATIONS" ]; then
    echo -e "${GREEN}✓ No migration files found${NC}"
    exit 0
fi

MIGRATION_COUNT=0
APPLIED_COUNT=0
SKIPPED_COUNT=0
FAILED_COUNT=0

# Process each migration
while IFS= read -r migration; do
    if [ -n "$migration" ]; then
        MIGRATION_COUNT=$((MIGRATION_COUNT + 1))
        MIGRATION_NAME=$(basename "$migration")
        
        echo -e "${BLUE}[$MIGRATION_COUNT] ${MIGRATION_NAME}${NC}"
        
        # Run the migration and capture output
        if docker-compose exec -T ${APP_NAME} python "$migration" 2>&1 | tee /tmp/migration_output_${MIGRATION_COUNT}.txt; then
            # Check if migration was skipped or applied
            if grep -qE "already exists|Skipping migration|Migration not needed" /tmp/migration_output_${MIGRATION_COUNT}.txt; then
                echo -e "    ${GREEN}↳ Already applied / Skipped${NC}"
                SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            else
                echo -e "    ${GREEN}↳ Applied successfully${NC}"
                APPLIED_COUNT=$((APPLIED_COUNT + 1))
            fi
        else
            echo -e "    ${RED}↳ Failed${NC}"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            echo ""
            echo -e "${RED}Migration failed. Check output above for details.${NC}"
            echo "Output saved to: /tmp/migration_output_${MIGRATION_COUNT}.txt"
            echo ""
            echo "Options:"
            echo "  1. Review the error and fix manually"
            echo "  2. Restore backup: tar -xzf ${BACKUP_FILE}"
            echo "  3. Continue with remaining migrations (not recommended)"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Aborting migration process"
                exit 1
            fi
        fi
        echo ""
        
        # Clean up temp file
        rm -f /tmp/migration_output_${MIGRATION_COUNT}.txt
    fi
done <<< "$MIGRATIONS"

# Summary
echo "=========================="
echo -e "${BLUE}Migration Summary${NC}"
echo "=========================="
echo "Total migrations found: ${MIGRATION_COUNT}"
echo -e "Applied: ${GREEN}${APPLIED_COUNT}${NC}"
echo -e "Skipped: ${YELLOW}${SKIPPED_COUNT}${NC}"
if [ $FAILED_COUNT -gt 0 ]; then
    echo -e "Failed: ${RED}${FAILED_COUNT}${NC}"
fi
echo ""

if [ $FAILED_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All migrations completed successfully${NC}"
    echo ""
    echo "Backup saved to: ${BACKUP_FILE}"
    echo "You can delete old backups from: ${BACKUP_DIR}/"
else
    echo -e "${RED}⚠ Some migrations failed${NC}"
    echo "Please review the errors above and take appropriate action"
    exit 1
fi

echo ""
echo "To verify database changes:"
echo "  docker-compose exec ${APP_NAME} python -c \"import sqlite3; conn = sqlite3.connect('/app/data/homebrew.db'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\\\"table\\\"'); print([r[0] for r in cursor.fetchall()])\""
echo ""
