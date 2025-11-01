# Vendly API - Complete CI/CD Deployment Guide

Complete guide for deploying Vendly FastAPI application to AWS EC2 with Docker, Caddy, and GitHub Actions.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS EC2 Setup](#aws-ec2-setup)
3. [Server Configuration](#server-configuration)
4. [Docker Setup](#docker-setup)
5. [GitHub Actions Setup](#github-actions-setup)
6. [Domain & SSL Setup](#domain--ssl-setup)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Prerequisites

Before starting, ensure you have:

- **AWS Account** with EC2 access
- **Domain name** (optional, for SSL/HTTPS)
- **GitHub account** with repository access
- **Docker Hub account** ([Sign up free](https://hub.docker.com/))
- **Basic Linux/SSH knowledge**
- **Git installed locally**

---

## 🖥️ AWS EC2 Setup

### Step 1: Launch EC2 Instance

1. **Go to AWS EC2 Console**
   - Login to [AWS Console](https://console.aws.amazon.com/)
   - Navigate to EC2 → Instances → Launch Instance

2. **Configure Instance:**
   ```
   Name and tags:
     Name: vendly-api-server
   
   Application and OS Images (Amazon Machine Image):
     AMI: Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
     Architecture: 64-bit (x86)
   
   Instance type:
     Type: t3.small (2 vCPU, 2 GB RAM) - Minimum recommended
     Alternative: t3.medium (2 vCPU, 4 GB RAM) - Better for production
   
   Key pair (login):
     Create new key pair:
       Name: vendly-key
       Type: RSA
       Format: .pem (for SSH)
     Download the .pem file and save it securely
   
   Network settings:
     VPC: Default (or your custom VPC)
     Auto-assign public IP: Enable
     Firewall (security group): Create new
   
   Configure storage:
     Root volume: 20 GB gp3 (or gp2)
   ```

3. **Security Group Configuration:**
   
   Create a new security group with these rules:
   
   | Type | Protocol | Port Range | Source | Description |
   |------|----------|------------|--------|-------------|
   | SSH | TCP | 22 | My IP | SSH access (your IP only) |
   | HTTP | TCP | 80 | 0.0.0.0/0, ::/0 | Public HTTP access |
   | HTTPS | TCP | 443 | 0.0.0.0/0, ::/0 | Public HTTPS access |
   | Custom TCP | TCP | 8000 | 0.0.0.0/0 | Direct API access (optional) |

   **Security Best Practice:** For SSH (port 22), use "My IP" instead of "0.0.0.0/0" to restrict access to your IP only.

4. **Launch Instance**
   - Click "Launch instance"
   - Download the `.pem` key file (you'll need this for SSH)

5. **Set Key Permissions:**

   **On Windows (PowerShell):**
   ```powershell
   # Navigate to where you saved the key
   cd C:\Users\YourUsername\Downloads
   
   # Remove inheritance and grant only your user read access
   icacls vendly-key.pem /inheritance:r
   icacls vendly-key.pem /grant:r "$($env:USERNAME):(R)"
   ```

   **On Linux/Mac:**
   ```bash
   chmod 400 vendly-key.pem
   ```

6. **Note Your EC2 Public IP:**
   - Go to EC2 Dashboard → Instances
   - Find your instance and copy the "Public IPv4 address"
   - Example: `54.123.45.678`

### Step 2: Connect to EC2

**From Windows (PowerShell):**
```powershell
ssh -i C:\Users\YourUsername\Downloads\vendly-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

**From Linux/Mac:**
```bash
ssh -i ~/Downloads/vendly-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

If you see a warning about authenticity, type `yes` and press Enter.

---

## ⚙️ Server Configuration

### Step 1: Update System

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install basic utilities
sudo apt install -y curl wget git vim htop
```

### Step 2: Install Docker

```bash
# Download Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh

# Run the installation script
sudo sh get-docker.sh

# Add current user to docker group (to run docker without sudo)
sudo usermod -aG docker $USER

# Apply group changes (logout and login)
exit
```

**SSH back in:**
```bash
ssh -i vendly-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

**Verify Docker installation:**
```bash
docker --version
docker ps
```

### Step 3: Install Docker Compose

```bash
# Install Docker Compose
sudo apt install docker-compose -y

# Verify installation
docker-compose --version
```

### Step 4: Configure Git

```bash
# Set your Git identity
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"

# Optional: Generate SSH key for GitHub
ssh-keygen -t ed25519 -C "your-email@example.com"

# Display public key to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

**Add SSH key to GitHub:**
1. Copy the output of the `cat` command
2. Go to GitHub → Settings → SSH and GPG keys → New SSH key
3. Paste the key and save

### Step 5: Clone Your Repository

```bash
# Navigate to home directory
cd ~

# Clone using HTTPS (easier)
git clone https://github.com/OriD-19/vendly_backend.git vendly

# OR clone using SSH (if you set up SSH key)
git clone git@github.com:OriD-19/vendly_backend.git vendly

# Navigate to the repository
cd vendly
```

### Step 6: Create Environment File

```bash
# Create .env file
nano .env
```

**Add your environment variables:**

```bash
# ===== Database Configuration (Supabase PostgreSQL) =====
# Option 1: Full connection URL (recommended for Supabase)
DATABASE_URL=postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Option 2: Individual components (if not using DATABASE_URL)
# DB_TYPE=postgresql
# DB_HOST=aws-0-us-east-1.pooler.supabase.com
# DB_PORT=6543
# DB_USER=postgres.xxxxx
# DB_PASSWORD=your-password
# DB_NAME=postgres

# ===== JWT Authentication =====
# Generate with: openssl rand -hex 32
SECRET_KEY=your-super-secret-key-minimum-32-characters-long-change-this-in-production
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

# ===== Optional: Logging =====
LOG_LEVEL=INFO
```

**Save and exit:**
- Press `Ctrl+X`
- Press `Y` to confirm
- Press `Enter` to save

**Secure the .env file:**
```bash
chmod 600 .env
```

---

## 🐳 Docker Setup

### Step 1: Build Docker Image

```bash
# Ensure you're in the vendly directory
cd ~/vendly

# Build the Docker image
docker-compose build

# This will take a few minutes on first build
```

### Step 2: Start Services

```bash
# Start all services in detached mode
docker-compose up -d

# This starts:
# - vendly-api (FastAPI application)
# - vendly-caddy (Reverse proxy)
```

### Step 3: Check Status

```bash
# Check running containers
docker-compose ps

# Should show:
# NAME            STATUS          PORTS
# vendly-api      Up (healthy)    0.0.0.0:8000->8000/tcp
# vendly-caddy    Up              0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api
docker-compose logs -f caddy

# Press Ctrl+C to exit logs
```

### Step 4: Initialize Database

```bash
# Run database initialization
docker-compose exec api python init_db.py

# Expected output:
# ✅ Database initialized successfully

# Optional: Seed with mock data
docker-compose exec api python seed_database.py
```

### Step 5: Test the API

```bash
# Test from EC2 instance (local)
curl http://localhost/

# Expected response:
# {"message":"Welcome to Vendly API"}

# Test direct API port
curl http://localhost:8000/

# View API documentation
curl http://localhost/docs
```

**Test from your computer:**
```bash
# Replace with your EC2 public IP
curl http://YOUR_EC2_PUBLIC_IP/
```

If this works, your API is live! 🎉

---

## 🔄 GitHub Actions Setup

### Step 1: Create Docker Hub Repository

1. Go to [Docker Hub](https://hub.docker.com/)
2. Click "Create Repository"
3. Repository name: `vendly-api`
4. Visibility: Public (or Private if you have a paid plan)
5. Click "Create"

### Step 2: Generate Docker Hub Access Token

1. Docker Hub → Account Settings → Security
2. Click "New Access Token"
3. Description: `GitHub Actions`
4. Access permissions: Read, Write, Delete
5. Click "Generate"
6. **Copy the token** (you won't see it again!)

### Step 3: Add GitHub Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"

Add these secrets one by one:

| Secret Name | Value | Example |
|------------|-------|---------|
| `DOCKER_USERNAME` | Your Docker Hub username | `johndoe` |
| `DOCKER_PASSWORD` | Docker Hub access token | `dckr_pat_xxxxx...` |
| `EC2_HOST` | EC2 public IP address | `54.123.45.678` |
| `EC2_USERNAME` | EC2 user (usually `ubuntu`) | `ubuntu` |
| `EC2_SSH_KEY` | Contents of your .pem file | `-----BEGIN RSA PRIVATE KEY-----...` |

**For EC2_SSH_KEY:**
```bash
# On Windows (PowerShell):
Get-Content C:\Users\YourUsername\Downloads\vendly-key.pem | clip

# On Linux/Mac:
cat ~/Downloads/vendly-key.pem | pbcopy  # Mac
cat ~/Downloads/vendly-key.pem | xclip   # Linux
```

Paste the entire contents including the header and footer lines.

### Step 4: Test GitHub Actions

```bash
# Make a small change to test deployment
echo "# CI/CD Pipeline Configured" >> README.md

# Commit and push
git add .
git commit -m "Configure CI/CD pipeline"
git push origin master
```

**Monitor the deployment:**
1. Go to GitHub → Your repository
2. Click "Actions" tab
3. You should see a workflow running
4. Click on it to see the progress

The workflow will:
1. ✅ Run tests and linting
2. ✅ Build Docker image
3. ✅ Push to Docker Hub
4. ✅ SSH to EC2 and deploy
5. ✅ Run health checks

**Deployment takes ~5-10 minutes** on the first run.

---

## 🌐 Domain & SSL Setup

### Option 1: Using Caddy (Recommended - Automatic SSL)

#### Prerequisites:
- Domain name (e.g., `api.yourdomain.com`)
- Domain pointed to your EC2 IP

#### Step 1: Configure DNS

Add an A record in your domain registrar:

```
Type: A
Name: api
Value: YOUR_EC2_PUBLIC_IP
TTL: 300
```

Wait 5-10 minutes for DNS propagation. Verify:
```bash
nslookup api.yourdomain.com
```

#### Step 2: Update Caddyfile

```bash
# On EC2 instance
cd ~/vendly
nano Caddyfile
```

**Replace the entire contents with:**

```
{
    email your-email@example.com
}

api.yourdomain.com {
    reverse_proxy api:8000
    encode gzip
    
    tls your-email@example.com
    
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
    
    log {
        output file /data/logs/access.log {
            roll_size 100mb
            roll_keep 5
        }
        format json
    }
}
```

Replace `api.yourdomain.com` and `your-email@example.com` with your actual values.

#### Step 3: Restart Caddy

```bash
docker-compose restart caddy

# Watch logs to see SSL certificate generation
docker-compose logs -f caddy
```

You should see:
```
✅ Certificate obtained successfully
```

#### Step 4: Test HTTPS

```bash
curl https://api.yourdomain.com/
```

Your API is now live with automatic HTTPS! 🎉

### Option 2: Using Nginx + Certbot

If you prefer Nginx over Caddy:

```bash
# Create nginx configuration
nano nginx.conf
```

Add:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name api.yourdomain.com;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

Then install Certbot for SSL (manual process).

---

## 📊 Monitoring & Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f caddy

# Last 100 lines
docker-compose logs --tail=100 api

# Follow logs with timestamp
docker-compose logs -f --timestamps api
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
docker-compose restart caddy

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Rebuild and restart
docker-compose up -d --build
```

### Update Application Manually

```bash
cd ~/vendly

# Pull latest code
git pull origin master

# Rebuild and restart
docker-compose up -d --build

# Or use the deployment script
chmod +x deploy.sh
./deploy.sh
```

### Monitor System Resources

```bash
# Real-time container stats
docker stats

# Disk usage
df -h
docker system df

# Memory usage
free -h

# CPU and memory (interactive)
htop
```

### Database Management

```bash
# Access Python shell in API container
docker-compose exec api python

# Then in Python:
from app.database import SessionLocal
from app.models.user import User
db = SessionLocal()
users = db.query(User).all()
print(f"Total users: {len(users)}")
```

### Clean Up Resources

```bash
# Remove unused containers, networks, images
docker system prune -a

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes (be careful!)
docker volume prune
```

### Automated Backups

Create a backup script:

```bash
nano backup.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup .env file
cp ~/vendly/.env $BACKUP_DIR/env_$DATE.backup

echo "Backup completed: $BACKUP_DIR/env_$DATE.backup"
```

Make it executable:
```bash
chmod +x backup.sh
```

Schedule with cron:
```bash
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /home/ubuntu/backup.sh
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. **Port Already in Use**

```bash
# Find process using port 80
sudo lsof -i :80

# Find process using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or stop all Docker containers
docker-compose down
```

#### 2. **Docker Permission Denied**

```bash
# If you see "permission denied" errors:
sudo usermod -aG docker $USER

# Then logout and login again
exit
ssh -i vendly-key.pem ubuntu@YOUR_EC2_IP
```

#### 3. **Database Connection Failed**

```bash
# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection from container
docker-compose exec api python -c "from app.database import engine; print(engine.url)"

# Check if Supabase allows your EC2 IP
# Go to Supabase → Project Settings → Database → Connection Pooling
# Ensure connection pooler is enabled
```

#### 4. **SSL Certificate Not Working**

```bash
# Check Caddy logs
docker-compose logs caddy

# Common issues:
# - Domain not pointing to EC2 IP (check DNS)
# - Port 443 not open in security group
# - Email address not valid in Caddyfile

# Force SSL renewal
docker-compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

#### 5. **GitHub Actions Deployment Failed**

```bash
# Check GitHub Actions logs for details

# Common issues:
# - SSH key not formatted correctly (include header/footer)
# - EC2 security group doesn't allow SSH from GitHub IPs
# - Docker credentials incorrect

# Test SSH connection manually
ssh -i vendly-key.pem ubuntu@YOUR_EC2_IP "docker ps"
```

#### 6. **API Returns 502 Bad Gateway**

```bash
# Check if API container is running
docker-compose ps

# Check API logs
docker-compose logs api

# Restart API
docker-compose restart api

# Check if API is responding internally
docker-compose exec api curl http://localhost:8000/
```

#### 7. **Out of Disk Space**

```bash
# Check disk usage
df -h

# Clean up Docker resources
docker system prune -a --volumes

# Check logs size
sudo du -sh /var/lib/docker/containers/*

# Limit log size in docker-compose.yml (already configured)
```

### Health Checks

```bash
# API health
curl http://localhost/
curl http://YOUR_EC2_PUBLIC_IP/
curl https://api.yourdomain.com/  # If SSL configured

# Docker health
docker ps
docker-compose ps

# Check specific container health
docker inspect vendly-api | grep -A 10 Health

# System health
top
free -h
df -h

# Network connectivity
ping google.com
curl https://api.github.com
```

### Debug Mode

```bash
# Stop containers
docker-compose down

# Start in foreground with logs
docker-compose up

# Press Ctrl+C to stop

# Run API container with shell access
docker-compose run --rm api /bin/bash
```

---

## 📝 Deployment Checklist

Use this checklist for each deployment:

- [ ] EC2 instance created and running
- [ ] Security groups configured (ports 22, 80, 443)
- [ ] SSH access working from local machine
- [ ] Docker and Docker Compose installed on EC2
- [ ] Repository cloned to `/home/ubuntu/vendly`
- [ ] `.env` file created with all required secrets
- [ ] Docker containers built successfully
- [ ] Containers running (`docker-compose ps` shows healthy)
- [ ] Database initialized (`python init_db.py`)
- [ ] API responding on `http://localhost/`
- [ ] API responding on `http://EC2_PUBLIC_IP/`
- [ ] Docker Hub repository created
- [ ] GitHub Secrets configured (5 secrets)
- [ ] GitHub Actions workflow runs successfully
- [ ] Deployment completes without errors
- [ ] Health checks pass
- [ ] Domain pointed to EC2 IP (optional)
- [ ] SSL configured with Caddy (optional)
- [ ] HTTPS working (optional)
- [ ] Monitoring and logging setup
- [ ] Backup strategy implemented

---

## 🎉 Success!

Your Vendly API is now:
- ✅ Running on AWS EC2
- ✅ Containerized with Docker
- ✅ Behind Caddy reverse proxy with automatic HTTPS
- ✅ Auto-deploying on every push to main branch
- ✅ Production-ready and scalable

### **API Endpoints:**
- **Health:** `http://YOUR_EC2_IP/` or `https://api.yourdomain.com/`
- **Documentation:** `http://YOUR_EC2_IP/docs`
- **OpenAPI Schema:** `http://YOUR_EC2_IP/openapi.json`
- **API Base:** `http://YOUR_EC2_IP/api/*`

### **Next Steps:**
1. Set up monitoring (CloudWatch, Datadog, etc.)
2. Configure automated backups
3. Implement CI/CD for staging environment
4. Add more comprehensive tests
5. Set up log aggregation
6. Configure alerts and notifications
7. Implement rate limiting
8. Add API versioning
9. Set up CDN for static assets
10. Implement blue-green deployments

---

## 📚 Additional Resources

- [FastAPI Deployment Documentation](https://fastapi.tiangolo.com/deployment/)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## 🆘 Support

If you encounter issues not covered in this guide:

1. **Check logs:** `docker-compose logs -f`
2. **Review GitHub Actions:** Check the Actions tab for deployment logs
3. **Check EC2 Console:** Verify instance is running and healthy
4. **Review Security Groups:** Ensure ports are open
5. **Test connectivity:** Use `curl` and `telnet` to debug network issues

---

**Happy Deploying! 🚀**
