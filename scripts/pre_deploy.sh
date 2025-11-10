#!/bin/bash

# Pre-deployment script to ensure clean database state
# Run this on EC2 before deploying if you're experiencing connection issues

set -e

echo "========================================="
echo "PRE-DEPLOYMENT DATABASE CLEANUP"
echo "========================================="
echo ""

cd /home/ubuntu/vendly || cd ~/vendly

# Stop containers gracefully
echo "🛑 Stopping containers..."
docker-compose down --timeout 30 2>/dev/null || true

# Wait for connections to close
echo "⏳ Waiting for database connections to close (10 seconds)..."
sleep 10

# Clean up any orphaned containers
echo "🧹 Cleaning up Docker..."
docker container prune -f
docker network prune -f

# Optional: Close database connections programmatically
if [ -f "scripts/close_db_connections.py" ]; then
    echo ""
    echo "🔌 Closing idle database connections..."
    python3 scripts/close_db_connections.py || echo "⚠️  Could not close DB connections (script failed)"
fi

echo ""
echo "✅ Pre-deployment cleanup complete!"
echo ""
echo "You can now run: docker-compose up -d"
echo ""
