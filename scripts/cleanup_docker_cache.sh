#!/bin/bash
# scripts/cleanup_docker_cache.sh
# Cleans Docker build cache and dangling images to free up space.
# Designed to run on system startup.

# Wait for Docker to be ready
until docker info > /dev/null 2>&1; do
  echo "Waiting for Docker to start..."
  sleep 5
done

echo "Docker is ready. Starting cleanup..."

# Prune dangling images (safe, removes unused layers)
docker image prune -f

# Prune build cache (removes all build cache)
# This frees the most space but makes the next build slower.
docker builder prune -a -f

echo "Docker cleanup complete."
