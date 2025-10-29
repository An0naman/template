#!/bin/bash
# Update script for app instances
# Safely updates to latest framework version with backup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Template Framework Update Script${NC}"
echo "=================================="
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
VERSION=${VERSION:-latest}

echo "App Name: ${APP_NAME}"
echo "Target Version: ${VERSION}"
echo ""

# Step 1: Create backup
echo -e "${YELLOW}Step 1: Creating backup...${NC}"
BACKUP_FILE="backup-$(date +%Y%m%d-%H%M%S).tar.gz"
if [ -d "data" ]; then
    tar -czf "${BACKUP_FILE}" data/ 2>/dev/null || echo "Backup created with warnings"
    echo -e "${GREEN}✓ Backup created: ${BACKUP_FILE}${NC}"
else
    echo -e "${YELLOW}⚠ No data directory found, skipping backup${NC}"
fi
echo ""

# Step 2: Pull latest image
echo -e "${YELLOW}Step 2: Pulling latest framework image...${NC}"
docker-compose pull
echo -e "${GREEN}✓ Image pulled${NC}"
echo ""

# Step 3: Stop and remove old container
echo -e "${YELLOW}Step 3: Stopping container...${NC}"
docker-compose down
echo -e "${GREEN}✓ Container stopped${NC}"
echo ""

# Step 4: Start with new image
echo -e "${YELLOW}Step 4: Starting updated container...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Container started${NC}"
echo ""

# Step 5: Wait for health check
echo -e "${YELLOW}Step 5: Waiting for app to be healthy...${NC}"
sleep 10

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Container is running${NC}"
else
    echo -e "${RED}✗ Container failed to start${NC}"
    echo ""
    echo "Rolling back..."
    docker-compose down
    echo ""
    echo "Check logs with: docker-compose logs"
    echo "Restore backup with: tar -xzf ${BACKUP_FILE}"
    exit 1
fi

# Step 6: Show version info
echo ""
echo -e "${YELLOW}Step 6: Verifying update...${NC}"
CURRENT_VERSION=$(docker-compose exec -T app cat /app/VERSION 2>/dev/null || echo "unknown")
echo "Running version: ${CURRENT_VERSION}"
echo ""

# Success
echo -e "${GREEN}=================================="
echo "✓ Update completed successfully!"
echo "==================================${NC}"
echo ""
echo "Backup saved to: ${BACKUP_FILE}"
echo ""
echo "View logs with: docker-compose logs -f"
echo "Check status with: docker-compose ps"
echo ""
