#!/bin/bash
set -e

# ReadReceipt Docker Entrypoint Script
# Handles database migrations and startup

echo "🚀 Starting ReadReceipt..."

# Run database migrations if flask-migrate is available
if command -v flask &> /dev/null; then
    echo "📊 Running database migrations..."
    cd /app
    flask --app src/readreceipt/app.py db upgrade || echo "⚠️  Migration skipped (may be first run or using in-memory DB)"
fi

# Check if ADMIN_TOKEN is still the default
if [ "$ADMIN_TOKEN" = "change-me-in-production" ]; then
    echo "⚠️  WARNING: Using default ADMIN_TOKEN. Please set a secure token in production!"
fi

echo "✅ ReadReceipt is ready!"
echo "🌐 Server starting on port $PORT"

# Execute the main command
exec "$@"
