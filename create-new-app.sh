#!/bin/bash
# Quick script to create a new app instance from the template

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Template Framework - New App Creator     ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo ""

# Get app name
echo -e "${YELLOW}What do you want to call this app?${NC}"
echo -e "  Examples: homebrews, inventory, recipes, tasks"
read -p "App name: " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo -e "${RED}Error: App name cannot be empty${NC}"
    exit 1
fi

# Get port
echo ""
echo -e "${YELLOW}What port should this app use?${NC}"
echo -e "  Current apps:"
ls ~/apps/ 2>/dev/null | while read app; do
    if [ -f ~/apps/$app/.env ]; then
        PORT=$(grep "^PORT=" ~/apps/$app/.env | cut -d'=' -f2)
        echo -e "    - ${app}: port ${PORT}"
    fi
done
echo ""
read -p "Port (e.g., 5003): " PORT

if [ -z "$PORT" ]; then
    echo -e "${RED}Error: Port cannot be empty${NC}"
    exit 1
fi

# Create directory
APP_DIR=~/apps/${APP_NAME}
if [ -d "$APP_DIR" ]; then
    echo -e "${RED}Error: Directory $APP_DIR already exists${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Creating new app: ${APP_NAME}${NC}"
mkdir -p "$APP_DIR"

# Get template path
TEMPLATE_DIR="$(cd "$(dirname "$0")/app-instance-template" && pwd)"

# Copy files
echo -e "${GREEN}→ Copying template files...${NC}"
cp "$TEMPLATE_DIR/docker-compose.yml" "$APP_DIR/"
cp "$TEMPLATE_DIR/.env.example" "$APP_DIR/.env"
cp "$TEMPLATE_DIR/.gitignore" "$APP_DIR/"
cp "$TEMPLATE_DIR/backup.sh" "$APP_DIR/"
cp "$TEMPLATE_DIR/update.sh" "$APP_DIR/"
cp "$TEMPLATE_DIR/run-migrations.sh" "$APP_DIR/"
cp "$TEMPLATE_DIR/README.md" "$APP_DIR/"

# Make scripts executable
chmod +x "$APP_DIR/backup.sh"
chmod +x "$APP_DIR/update.sh"
chmod +x "$APP_DIR/run-migrations.sh"

# Configure .env file
echo -e "${GREEN}→ Configuring environment...${NC}"
sed -i "s/^APP_NAME=.*/APP_NAME=${APP_NAME}/" "$APP_DIR/.env"
sed -i "s/^PORT=.*/PORT=${PORT}/" "$APP_DIR/.env"

# Create data directory
mkdir -p "$APP_DIR/data"

echo ""
echo -e "${GREEN}✓ App created successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Review configuration:"
echo -e "     ${YELLOW}nano ~/apps/${APP_NAME}/.env${NC}"
echo ""
echo -e "  2. Start the app:"
echo -e "     ${YELLOW}cd ~/apps/${APP_NAME}${NC}"
echo -e "     ${YELLOW}docker-compose pull${NC}"
echo -e "     ${YELLOW}docker-compose up -d${NC}"
echo ""
echo -e "  3. Access the app:"
echo -e "     ${YELLOW}http://localhost:${PORT}${NC}"
echo -e "     ${YELLOW}http://$(hostname -I | awk '{print $1}'):${PORT}${NC}"
echo ""
echo -e "  4. View logs:"
echo -e "     ${YELLOW}cd ~/apps/${APP_NAME} && docker-compose logs -f${NC}"
echo ""
echo -e "${GREEN}✓ Your app will auto-update when you push to GitHub!${NC}"
