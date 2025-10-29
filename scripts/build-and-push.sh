#!/bin/bash
# Build and push Docker image manually
# Usage: ./scripts/build-and-push.sh [version]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="ghcr.io"
REPO_OWNER="an0naman"
IMAGE_NAME="template"
FULL_IMAGE="${REGISTRY}/${REPO_OWNER}/${IMAGE_NAME}"

# Get version from argument or use 'dev'
VERSION="${1:-dev}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD)

echo -e "${GREEN}Building Docker image for framework${NC}"
echo "=================================="
echo "Image: ${FULL_IMAGE}"
echo "Version: ${VERSION}"
echo "Build Date: ${BUILD_DATE}"
echo "Git Commit: ${VCS_REF}"
echo "=================================="
echo ""

# Build multi-architecture image
echo -e "${YELLOW}Building for multiple architectures (amd64, arm64)...${NC}"
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${VCS_REF}" \
    --build-arg VERSION="${VERSION}" \
    -f Dockerfile.optimized \
    -t "${FULL_IMAGE}:${VERSION}" \
    -t "${FULL_IMAGE}:latest" \
    --push \
    .

echo ""
echo -e "${GREEN}✓ Build and push completed successfully!${NC}"
echo ""
echo "Available tags:"
echo "  ${FULL_IMAGE}:${VERSION}"
echo "  ${FULL_IMAGE}:latest"
echo ""
echo "To pull this image:"
echo "  docker pull ${FULL_IMAGE}:${VERSION}"
echo "  docker pull ${FULL_IMAGE}:latest"
echo ""
echo "To use in docker-compose.yml:"
echo "  image: ${FULL_IMAGE}:${VERSION}"
