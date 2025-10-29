#!/bin/bash
# Docker Cleanup and Test App Creation Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Docker Cleanup & Test App Creation                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Show current state
echo -e "${YELLOW}Current Docker State:${NC}"
docker system df
echo ""

# Show running containers
echo -e "${YELLOW}Running Containers:${NC}"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Step 1: Review what to keep
echo -e "${GREEN}=== Step 1: Review Running Apps ===${NC}"
echo ""
echo "Keep these apps?"
echo -e "${GREEN}  ✓ template${NC} - Main template app (likely on port 5001)"
echo -e "${GREEN}  ✓ botany${NC} - Botany app (port 5004)"
echo -e "${GREEN}  ✓ 3d-printing${NC} - 3D Printing app (port 5003)"
echo -e "${GREEN}  ✓ godot${NC} - Godot app (port 5002)"
echo -e "${BLUE}  ? immich-*${NC} - Photo management (Immich)"
echo ""

read -p "Do you want to keep the Immich apps? (y/n): " keep_immich

# Step 2: Stop and remove unwanted containers
if [[ "$keep_immich" != "y" ]]; then
    echo ""
    echo -e "${YELLOW}Stopping and removing Immich containers...${NC}"
    docker stop immich-server immich-machine-learning immich-redis immich-postgres 2>/dev/null || true
    docker rm immich-server immich-machine-learning immich-redis immich-postgres 2>/dev/null || true
    echo -e "${GREEN}✓ Immich containers removed${NC}"
fi

# Step 3: Remove dangling images
echo ""
echo -e "${GREEN}=== Step 2: Cleanup Dangling Images ===${NC}"
echo ""
echo "You have $(docker images -f 'dangling=true' -q | wc -l) dangling images (353 old builds)"
echo "These are old, unused image layers taking up ~5.8GB"
echo ""
read -p "Remove all dangling images? (y/n): " remove_dangling

if [[ "$remove_dangling" == "y" ]]; then
    echo -e "${YELLOW}Removing dangling images...${NC}"
    docker image prune -f
    echo -e "${GREEN}✓ Dangling images removed${NC}"
fi

# Step 4: Remove unused volumes
echo ""
echo -e "${GREEN}=== Step 3: Cleanup Unused Volumes ===${NC}"
echo ""
echo "Current volumes:"
docker volume ls
echo ""
echo "Unused volumes (likely from deleted test apps):"
docker volume ls -qf dangling=true
echo ""
read -p "Remove unused volumes? (y/n): " remove_volumes

if [[ "$remove_volumes" == "y" ]]; then
    echo -e "${YELLOW}Removing unused volumes...${NC}"
    docker volume prune -f
    echo -e "${GREEN}✓ Unused volumes removed${NC}"
fi

# Step 5: Remove build cache
echo ""
echo -e "${GREEN}=== Step 4: Cleanup Build Cache ===${NC}"
echo ""
echo "Build cache: 170.8MB"
read -p "Remove build cache? (y/n): " remove_cache

if [[ "$remove_cache" == "y" ]]; then
    echo -e "${YELLOW}Removing build cache...${NC}"
    docker builder prune -f
    echo -e "${GREEN}✓ Build cache removed${NC}"
fi

# Show final state
echo ""
echo -e "${GREEN}=== Cleanup Complete ===${NC}"
echo ""
echo -e "${YELLOW}New Docker State:${NC}"
docker system df
echo ""

# Step 6: Create test app
echo -e "${GREEN}=== Step 5: Create Test App ===${NC}"
echo ""
read -p "Create a test app instance? (y/n): " create_test

if [[ "$create_test" == "y" ]]; then
    echo ""
    echo -e "${YELLOW}Creating test app...${NC}"
    
    # Create test app directory
    TEST_DIR="$HOME/apps/test-framework"
    mkdir -p "$TEST_DIR"
    
    echo -e "${BLUE}Test app directory: $TEST_DIR${NC}"
    
    # Copy template files
    cp -r app-instance-template/* "$TEST_DIR/"
    cp app-instance-template/.env.example "$TEST_DIR/.env"
    cp app-instance-template/.gitignore "$TEST_DIR/"
    
    # Configure .env
    cat > "$TEST_DIR/.env" << 'EOF'
APP_NAME=test-framework
PORT=5010
VERSION=latest
DEBUG=false
NETWORK_RANGE=192.168.68.0/24
SECRET_KEY=test-secret-change-in-production
EOF
    
    echo -e "${GREEN}✓ Template files copied${NC}"
    echo -e "${GREEN}✓ Configured for port 5010${NC}"
    echo ""
    echo "Next steps:"
    echo "  cd $TEST_DIR"
    echo "  docker-compose up -d"
    echo "  Visit: http://localhost:5010"
    echo ""
    
    read -p "Start the test app now? (y/n): " start_now
    
    if [[ "$start_now" == "y" ]]; then
        cd "$TEST_DIR"
        docker-compose up -d
        echo ""
        echo -e "${GREEN}✓ Test app started!${NC}"
        echo ""
        echo "Check status: docker-compose ps"
        echo "View logs: docker-compose logs -f"
        echo "Access: http://localhost:5010"
    fi
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Cleanup Complete!                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
