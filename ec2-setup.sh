#!/bin/bash

# Vendly API - EC2 Initial Setup Script
# Run this script on a fresh Ubuntu 22.04 EC2 instance
# Usage: bash ec2-setup.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Functions for colored output
print_header() {
    echo ""
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
    echo ""
}

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

# Welcome message
clear
print_header "Vendly API - EC2 Setup Script"
echo "This script will set up your EC2 instance for Vendly API deployment."
echo ""
echo "It will install:"
echo "  • Docker"
echo "  • Docker Compose"
echo "  • Git"
echo "  • Required utilities"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Step 1: Update system
print_header "Step 1: Updating System"
print_info "Updating package lists..."
sudo apt update

print_info "Upgrading installed packages..."
sudo apt upgrade -y

print_info "Installing basic utilities..."
sudo apt install -y curl wget git vim htop net-tools

print_success "System updated successfully"

# Step 2: Install Docker
print_header "Step 2: Installing Docker"

if command -v docker &> /dev/null; then
    print_warning "Docker is already installed"
    docker --version
else
    print_info "Downloading Docker installation script..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    
    print_info "Installing Docker..."
    sudo sh get-docker.sh
    
    print_info "Adding current user to docker group..."
    sudo usermod -aG docker $USER
    
    rm get-docker.sh
    print_success "Docker installed successfully"
fi

# Step 3: Install Docker Compose
print_header "Step 3: Installing Docker Compose"

if command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose is already installed"
    docker-compose --version
else
    print_info "Installing Docker Compose..."
    sudo apt install docker-compose -y
    print_success "Docker Compose installed successfully"
fi

# Step 4: Configure Git
print_header "Step 4: Configuring Git"

read -p "Enter your Git name (e.g., John Doe): " git_name
read -p "Enter your Git email (e.g., john@example.com): " git_email

git config --global user.name "$git_name"
git config --global user.email "$git_email"

print_success "Git configured successfully"

# Step 5: Generate SSH key for GitHub (optional)
print_header "Step 5: SSH Key for GitHub (Optional)"

if [ -f ~/.ssh/id_ed25519 ]; then
    print_warning "SSH key already exists"
else
    read -p "Generate SSH key for GitHub? (y/n): " generate_ssh
    
    if [ "$generate_ssh" = "y" ]; then
        ssh-keygen -t ed25519 -C "$git_email" -f ~/.ssh/id_ed25519 -N ""
        
        echo ""
        print_success "SSH key generated!"
        print_info "Add this public key to GitHub (Settings → SSH and GPG keys):"
        echo ""
        cat ~/.ssh/id_ed25519.pub
        echo ""
        read -p "Press Enter after adding the key to GitHub..."
    fi
fi

# Step 6: Clone repository
print_header "Step 6: Cloning Repository"

if [ -d ~/vendly ]; then
    print_warning "Repository directory already exists at ~/vendly"
    read -p "Remove and re-clone? (y/n): " reclone
    
    if [ "$reclone" = "y" ]; then
        rm -rf ~/vendly
    else
        print_info "Skipping repository clone"
    fi
fi

if [ ! -d ~/vendly ]; then
    print_info "Choose clone method:"
    echo "  1) HTTPS (easier, no SSH key needed)"
    echo "  2) SSH (requires SSH key added to GitHub)"
    read -p "Enter choice (1 or 2): " clone_method
    
    if [ "$clone_method" = "1" ]; then
        git clone https://github.com/OriD-19/vendly_backend.git ~/vendly
    else
        git clone git@github.com:OriD-19/vendly_backend.git ~/vendly
    fi
    
    print_success "Repository cloned to ~/vendly"
fi

# Step 7: Create .env file
print_header "Step 7: Creating Environment File"

cd ~/vendly

if [ -f .env ]; then
    print_warning ".env file already exists"
    read -p "Overwrite? (y/n): " overwrite_env
    
    if [ "$overwrite_env" != "y" ]; then
        print_info "Keeping existing .env file"
        skip_env=true
    fi
fi

if [ "$skip_env" != true ]; then
    print_info "Creating .env file..."
    print_warning "You'll need to edit this file manually with your secrets"
    
    cat > .env << 'EOF'
# ===== Database Configuration =====
DATABASE_URL=postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# ===== JWT Authentication =====
SECRET_KEY=change-this-to-a-secure-random-string-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===== AWS S3 Configuration =====
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=your-secret-access-key-here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
S3_PRODUCT_IMAGES_FOLDER=product-images

# ===== Application Settings =====
DEBUG=False
CORS_ORIGINS=*
EOF

    chmod 600 .env
    print_success ".env file created at ~/vendly/.env"
    print_warning "IMPORTANT: Edit this file with your actual credentials!"
fi

# Step 8: Make deploy script executable
print_header "Step 8: Setting Permissions"

chmod +x deploy.sh
print_success "Deploy script made executable"

# Step 9: Build and start services
print_header "Step 9: Docker Services"

read -p "Build and start Docker services now? (y/n): " start_services

if [ "$start_services" = "y" ]; then
    print_info "Building Docker images (this may take a few minutes)..."
    docker-compose build
    
    print_info "Starting services..."
    docker-compose up -d
    
    print_info "Waiting for services to start..."
    sleep 10
    
    print_info "Container status:"
    docker-compose ps
    
    print_success "Services started!"
else
    print_info "Skipping service startup"
    print_warning "Run 'docker-compose up -d' manually when ready"
fi

# Step 10: Initialize database
if [ "$start_services" = "y" ]; then
    print_header "Step 10: Initialize Database"
    
    read -p "Initialize database tables now? (y/n): " init_db
    
    if [ "$init_db" = "y" ]; then
        print_info "Initializing database..."
        docker-compose exec api python init_db.py
        
        read -p "Seed database with mock data? (y/n): " seed_db
        
        if [ "$seed_db" = "y" ]; then
            print_info "Seeding database..."
            docker-compose exec api python seed_database.py
        fi
    fi
fi

# Step 11: Final checks
print_header "Setup Complete! 🎉"

print_success "EC2 instance setup completed successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "Next Steps:"
echo ""
echo "1. Edit .env file with your secrets:"
echo "   nano ~/vendly/.env"
echo ""
echo "2. Restart services after editing .env:"
echo "   cd ~/vendly && docker-compose restart"
echo ""
echo "3. Test the API:"
echo "   curl http://localhost/"
echo ""
echo "4. View logs:"
echo "   cd ~/vendly && docker-compose logs -f"
echo ""
echo "5. Configure GitHub Actions:"
echo "   • Add GitHub Secrets (see CI_CD_SETUP_SUMMARY.md)"
echo "   • Push to main branch to trigger deployment"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_warning "IMPORTANT: You need to logout and login again for Docker group changes to take effect!"
echo ""
print_info "Run: exit"
print_info "Then SSH back in: ssh -i vendly-key.pem ubuntu@YOUR_EC2_IP"
echo ""

print_info "Useful aliases added to your ~/.bashrc:"
echo ""

# Add useful aliases
cat >> ~/.bashrc << 'EOF'

# Vendly API Aliases
alias vendly='cd ~/vendly'
alias vup='cd ~/vendly && docker-compose up -d'
alias vdown='cd ~/vendly && docker-compose down'
alias vrestart='cd ~/vendly && docker-compose restart'
alias vlogs='cd ~/vendly && docker-compose logs -f'
alias vps='cd ~/vendly && docker-compose ps'
alias vstatus='cd ~/vendly && docker-compose ps && docker stats --no-stream'
alias vdeploy='cd ~/vendly && ./deploy.sh'
alias vapi='cd ~/vendly && docker-compose logs -f api'
alias vcaddy='cd ~/vendly && docker-compose logs -f caddy'
EOF

source ~/.bashrc

echo "  • vendly     - Go to project directory"
echo "  • vup        - Start services"
echo "  • vdown      - Stop services"
echo "  • vrestart   - Restart services"
echo "  • vlogs      - View all logs"
echo "  • vps        - Container status"
echo "  • vstatus    - Full status"
echo "  • vdeploy    - Deploy updates"
echo "  • vapi       - API logs"
echo "  • vcaddy     - Caddy logs"
echo ""

print_success "Setup script completed! 🚀"
echo ""

# Show public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo "Unable to detect")
if [ "$PUBLIC_IP" != "Unable to detect" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_success "Your API is accessible at:"
    echo ""
    echo "  http://$PUBLIC_IP/"
    echo "  http://$PUBLIC_IP/docs"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi
