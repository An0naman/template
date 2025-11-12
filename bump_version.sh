#!/bin/bash
# Manual version bump script
# Usage: ./bump_version.sh [major|minor|patch]

VERSION_FILE="VERSION"
APP_JSON="app.json"

# Check if VERSION file exists
if [ ! -f "$VERSION_FILE" ]; then
    echo "1.0.0" > "$VERSION_FILE"
    echo "Created VERSION file with initial version 1.0.0"
fi

# Read current version
current_version=$(cat "$VERSION_FILE")
echo "Current version: $current_version"

# Split version into major.minor.patch
IFS='.' read -r -a version_parts <<< "$current_version"
major="${version_parts[0]}"
minor="${version_parts[1]}"
patch="${version_parts[2]}"

# Determine which part to increment (default: patch)
bump_type="${1:-patch}"

case $bump_type in
    major)
        major=$((major + 1))
        minor=0
        patch=0
        ;;
    minor)
        minor=$((minor + 1))
        patch=0
        ;;
    patch)
        patch=$((patch + 1))
        ;;
    *)
        echo "❌ Invalid bump type: $bump_type"
        echo "Usage: $0 [major|minor|patch]"
        exit 1
        ;;
esac

# Create new version
new_version="${major}.${minor}.${patch}"

echo "New version: $new_version"

# Update VERSION file
echo "$new_version" > "$VERSION_FILE"
echo "✓ Updated VERSION file"

# Update app.json version
if [ -f "$APP_JSON" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/\"version\": \".*\"/\"version\": \"$new_version\"/" "$APP_JSON"
    else
        # Linux
        sed -i "s/\"version\": \".*\"/\"version\": \"$new_version\"/" "$APP_JSON"
    fi
    echo "✓ Updated app.json"
fi

echo ""
echo "Version bumped from $current_version to $new_version"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git diff"
echo "  2. Commit the changes: git add VERSION app.json && git commit -m 'chore: Bump version to $new_version'"
echo "  3. Push to remote: git push"
echo "  4. (Optional) Create a tag: git tag v$new_version && git push --tags"
