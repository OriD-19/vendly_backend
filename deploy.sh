#!/bin/bash

set -e

echo "🚀 Starting deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Pull latest code
print_info "Pulling latest code..."
git pull origin master || git pull origin main
print_success "Code updated"

# Pull latest Docker image
print_info "Pulling latest Docker image..."
docker-compose pull
print_success "Docker images updated"

# Stop old containers
print_info "Stopping old containers..."
docker-compose down
print_success "Old containers stopped"

# Start new containers
print_info "Starting new containers..."
docker-compose up -d
print_success "New containers started"

# Wait for services to be healthy
print_info "Waiting for services to be healthy..."
sleep 15

# Check health
print_info "Checking health..."
if curl -f http://localhost/ > /dev/null 2>&1; then
    print_success "Health check passed!"
else
    print_warning "Health check failed! Checking logs..."
    docker-compose logs --tail=50 api
    print_error "Deployment may have failed. Please check the logs above."
    exit 1
fi

# Clean up old images
print_info "Cleaning up old images..."
docker image prune -f
print_success "Cleanup completed"

# Show status
echo ""
echo "=================================="
print_success "Deployment completed successfully!"
echo "=================================="
echo ""

# Show container status
print_info "Container status:"
docker-compose ps

echo ""
print_info "Recent logs:"
docker-compose logs --tail=20

echo ""
print_success "✨ Deployment finished!"
echo ""
print_info "API URL: http://localhost/"
print_info "API Docs: http://localhost/docs"
echo ""
