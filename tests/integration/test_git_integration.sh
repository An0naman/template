#!/bin/bash
# Test the Git Integration Token-Based Discovery feature

echo "🔄 Rebuilding Docker container..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo ""
echo "⏳ Waiting for container to start..."
sleep 5

echo ""
echo "✅ Container started! Testing API..."

# Check if API is responding
if curl -s http://localhost:5000/api/git/repositories > /dev/null; then
    echo "✅ Git API is responding"
else
    echo "❌ Git API is not responding"
    exit 1
fi

echo ""
echo "📋 Testing workflow:"
echo "1. Go to http://localhost:5000/settings#git"
echo "2. Select GitHub or GitLab"
echo "3. Enter your Personal Access Token:"
echo "   - GitHub: https://github.com/settings/tokens (needs 'repo' scope)"
echo "   - GitLab: https://gitlab.com/-/profile/personal_access_tokens (needs 'read_api' and 'read_repository')"
echo "4. Click 'Discover Repositories'"
echo "5. Toggle repositories you want to track"
echo "6. Click 'Save Tracked Repositories'"
echo "7. You'll be redirected to dashboard with Git widget visible"
echo ""
echo "🔍 View logs:"
echo "docker logs -f \$(docker ps -q --filter ancestor=template-web)"
