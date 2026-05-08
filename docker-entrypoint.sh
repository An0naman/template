#!/bin/bash
set -e

echo "=== Starting Application Initialization ==="
echo "Date: $(date)"
echo "Working Directory: $(pwd)"

# Fix DNS resolution for Google APIs 
# Workaround for Docker DNS issues - add direct IP mapping
echo "🔧 Fixing DNS/hosts configuration for Google API connectivity..."

# Add Google API endpoint to /etc/hosts as fallback
# This ensures the app can reach Gemini API even if DNS fails
if ! grep -q "generativelanguage.googleapis.com" /etc/hosts 2>/dev/null; then
    echo "142.250.204.10 generativelanguage.googleapis.com" >> /etc/hosts
    echo "142.251.221.74 generativelanguage.googleapis.com" >> /etc/hosts
    echo "✅ Added Google API endpoint to /etc/hosts"
fi

# Also try to fix resolv.conf if possible (for host networking mode)
if [ -w /etc/resolv.conf ]; then
    echo "nameserver 8.8.8.8" > /etc/resolv.conf
    echo "nameserver 8.8.4.4" >> /etc/resolv.conf
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf
    echo "✅ DNS configured to use Google/Cloudflare DNS"
fi

# Function to run migrations
run_migrations() {
    local migrations_dir="$1"
    local migration_count=0
    
    if [ ! -d "$migrations_dir" ]; then
        echo "⚠️  Migrations directory not found: $migrations_dir"
        return 0
    fi
    
    echo "📂 Checking for migrations in: $migrations_dir"
    
    # Find all Python migration files (excluding __init__.py and __pycache__)
    for migration in "$migrations_dir"/*.py; do
        if [ -f "$migration" ]; then
            local basename=$(basename "$migration")
            
            # Skip __init__.py and files starting with underscore
            if [ "$basename" = "__init__.py" ] || [[ "$basename" == _* ]]; then
                continue
            fi
            
            echo "🔄 Running migration: $basename"
            
            if python "$migration"; then
                echo "✅ Migration completed: $basename"
                migration_count=$((migration_count + 1))
            else
                echo "❌ Migration failed: $basename"
                echo "⚠️  Continuing with remaining migrations..."
                # Don't exit on migration failure, continue with others
            fi
        fi
    done
    
    if [ $migration_count -eq 0 ]; then
        echo "ℹ️  No migrations found or executed in $migrations_dir"
    else
        echo "✅ Completed $migration_count migration(s) from $migrations_dir"
    fi
}

# Run migrations from both locations
echo ""
echo "=== Running Database Migrations ==="

# Skip SQLite migration scripts when using an external database (MariaDB)
if [ -n "$DATABASE_URL" ]; then
    echo "ℹ️  DATABASE_URL is set — skipping SQLite migration scripts (schema managed by MariaDB)"
else
# Check for migrations in /app/migrations (root level)
if [ -d "/app/migrations" ]; then
    echo "📍 Checking root migrations..."
    run_migrations "/app/migrations"
fi

# Check for migrations in /app/app/migrations (app package level)
if [ -d "/app/app/migrations" ]; then
    echo "📍 Checking app package migrations..."
    run_migrations "/app/app/migrations"
fi
fi

echo ""
echo "=== Migrations Complete ==="
echo ""

# Execute the main command (passed as arguments to this script)
echo "🚀 Starting application: $@"
exec "$@"
