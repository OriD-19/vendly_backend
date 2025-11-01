# Vendly - E-Commerce API Platform

[![Deploy to EC2](https://github.com/OriD-19/vendly_backend/actions/workflows/deploy.yml/badge.svg)](https://github.com/OriD-19/vendly_backend/actions/workflows/deploy.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

A complete, production-ready e-commerce API platform built with FastAPI, featuring multi-tenant architecture, real-time chat, cloud storage, and automated CI/CD deployment.

## 🚀 Features

- **Multi-Tenant Architecture** - Store owners can manage their own products and orders
- **Real-Time Chat** - WebSocket-based customer-store messaging
- **Cloud Storage** - AWS S3 integration for product images
- **Advanced Analytics** - Revenue tracking, sales reports, and customer insights
- **JWT Authentication** - Secure user authentication with refresh tokens
- **PostgreSQL Support** - Production-ready database with Supabase integration
- **RESTful APIs** - 70+ endpoints with comprehensive documentation
- **Automated CI/CD** - GitHub Actions deployment to AWS EC2
- **Docker Ready** - Containerized with Docker Compose
- **Automatic HTTPS** - Caddy reverse proxy with Let's Encrypt SSL

## 📚 Tech Stack

- **Framework:** FastAPI 0.104.1 with Pydantic v2
- **Database:** PostgreSQL (Supabase) with SQLAlchemy 2.0
- **Authentication:** JWT with bcrypt password hashing
- **Storage:** AWS S3 (boto3)
- **WebSockets:** For real-time chat functionality
- **Deployment:** Docker, Docker Compose, GitHub Actions
- **Reverse Proxy:** Caddy (automatic HTTPS)
- **Cloud:** AWS EC2, Supabase, AWS S3

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Repository                      │
│                (Automated CI/CD Pipeline)               │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ Push → Auto Deploy
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    AWS EC2 Instance                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Caddy (Reverse Proxy + Auto SSL)                 │ │
│  │            ↓                                       │ │
│  │  Vendly API (FastAPI + Uvicorn)                   │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                           │
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│  Supabase       │         │    AWS S3       │
│  (PostgreSQL)   │         │ (Product Images)│
└─────────────────┘         └─────────────────┘
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/OriD-19/vendly_backend.git
   cd vendly_backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Initialize database:**
   ```bash
   python init_db.py
   
   # Optional: Seed with mock data
   python seed_database.py
   ```

6. **Run the server:**
   ```bash
   # Development mode
   python main.py
   
   # Or with auto-reload
   fastapi dev app/main.py
   ```

7. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - OpenAPI: http://localhost:8000/openapi.json

### Docker Deployment

1. **Using Docker Compose:**
   ```bash
   # Build and start all services
   docker-compose up -d
   
   # Initialize database
   docker-compose exec api python init_db.py
   
   # Seed database (optional)
   docker-compose exec api python seed_database.py
   
   # View logs
   docker-compose logs -f
   
   # Stop services
   docker-compose down
   ```

2. **Access the API:**
   - API: http://localhost
   - Docs: http://localhost/docs

### Production Deployment (AWS EC2)

**Automated deployment via GitHub Actions** - Every push to `main`/`master` automatically deploys to EC2!

1. **Set up EC2 instance** (see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md))
2. **Configure GitHub Secrets:**
   - `DOCKER_USERNAME` - Docker Hub username
   - `DOCKER_PASSWORD` - Docker Hub access token
   - `EC2_HOST` - EC2 public IP
   - `EC2_USERNAME` - SSH username (usually `ubuntu`)
   - `EC2_SSH_KEY` - Private SSH key (.pem file contents)

3. **Push to deploy:**
   ```bash
   git add .
   git commit -m "Deploy to production"
   git push origin master
   ```

4. **Monitor deployment:**
   - GitHub Actions: https://github.com/OriD-19/vendly_backend/actions
   - API: http://YOUR_EC2_IP/

📖 **Detailed deployment guide:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)  
⚡ **Quick reference:** [DEPLOYMENT_QUICK_REF.md](DEPLOYMENT_QUICK_REF.md)  
📋 **Setup summary:** [CI_CD_SETUP_SUMMARY.md](CI_CD_SETUP_SUMMARY.md)

## 📖 API Documentation

### Services & Endpoints

| Service | Endpoints | Description |
|---------|-----------|-------------|
| **Authentication** | 6 | User registration, login, token refresh |
| **Users** | 6 | User management and profiles |
| **Stores** | 13 | Store management, analytics, search |
| **Products** | 20 | Product CRUD, search, filters, recommendations |
| **Categories** | 14 | Category management with hierarchies |
| **Orders** | 17 | Order management, tracking, analytics |
| **Chat** | 11 + WebSocket | Real-time messaging between customers and stores |

**Total: 87+ endpoints** with comprehensive OpenAPI documentation

### Key Features by Service

#### 🔐 Authentication
- JWT-based authentication with refresh tokens
- Secure password hashing (bcrypt)
- Role-based access control (Customer/Store Owner)

#### 👥 User Management
- Customer and store owner profiles
- User preferences and settings
- Profile updates and verification

#### 🏪 Store Management
- Multi-tenant store support
- Store analytics and insights
- Product inventory management
- Search and filtering

#### 📦 Product Management
- Full CRUD operations
- Image upload to AWS S3
- Advanced search and filtering
- Product recommendations
- Tag-based organization
- Category hierarchies

#### 🛒 Order Management
- Complete order lifecycle
- Order tracking and status updates
- Revenue analytics
- Customer order history
- Sales reports and insights

#### 💬 Real-Time Chat
- WebSocket-based messaging
- Customer-store communication
- Message history
- Unread message tracking

## 🗂️ Project Structure

```
vendly/
├── app/
│   ├── api/           # API route handlers
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── stores.py
│   │   ├── products.py
│   │   ├── categories.py
│   │   ├── orders.py
│   │   └── chat.py
│   ├── models/        # SQLAlchemy models
│   │   ├── user.py
│   │   ├── store.py
│   │   ├── product.py
│   │   ├── category.py
│   │   ├── order.py
│   │   └── chat_message.py
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── order.py
│   │   ├── store_service.py
│   │   ├── s3_service.py
│   │   └── chat_service.py
│   ├── middleware/    # Custom middleware
│   │   ├── auth.py
│   │   ├── cors.py
│   │   ├── error_handling.py
│   │   └── logging.py
│   ├── utils/         # Utility functions
│   ├── websockets/    # WebSocket handlers
│   ├── config.py      # Configuration
│   ├── database.py    # Database setup
│   └── main.py        # FastAPI app
├── .github/
│   └── workflows/
│       └── deploy.yml # CI/CD pipeline
├── Dockerfile         # Docker image definition
├── docker-compose.yml # Multi-container setup
├── Caddyfile         # Reverse proxy config
├── requirements.txt   # Python dependencies
├── init_db.py        # Database initialization
├── seed_database.py  # Mock data seeder
├── deploy.sh         # Deployment script
└── main.py           # Entry point
```

## 🔐 Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# JWT Authentication
SECRET_KEY=your-super-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
S3_PRODUCT_IMAGES_FOLDER=product-images

# Application
DEBUG=False
CORS_ORIGINS=*
```

See [`.env.example`](.env.example) for complete configuration.

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 📊 Database

### Supported Databases
- **Development:** SQLite (automatic fallback)
- **Production:** PostgreSQL (Supabase recommended)

### Database Commands

```bash
# Initialize database (create all tables)
python init_db.py

# Seed with mock data
python seed_database.py

# Access Python shell
docker-compose exec api python
>>> from app.database import SessionLocal
>>> from app.models.user import User
>>> db = SessionLocal()
>>> users = db.query(User).all()
```

### Mock Data
The seeder creates:
- 5 users (2 store owners, 3 customers)
- 2 stores (TechHub Electronics, Chic Fashion Boutique)
- 22 products across 8 categories
- 4 complete customer orders
- 8 chat messages
- Product images, tags, and relationships

**Login credentials:**
- Store Owners: `techstore_owner` / `storeowner123`, `fashion_boutique` / `storeowner123`
- Customers: `john_doe` / `customer123`, `jane_smith` / `customer123`, `mike_wilson` / `customer123`

## 🚀 Deployment

### GitHub Actions CI/CD

The repository includes a complete CI/CD pipeline that automatically:

1. ✅ Runs tests and linting
2. ✅ Builds Docker image
3. ✅ Pushes to Docker Hub
4. ✅ Deploys to EC2 via SSH
5. ✅ Runs health checks

**Trigger:** Every push to `main`/`master` branch

**Monitor:** https://github.com/OriD-19/vendly_backend/actions

### Manual Deployment

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Navigate to project
cd ~/vendly

# Deploy updates
./deploy.sh
```

### Useful Commands

```bash
# View logs
docker-compose logs -f api

# Restart services
docker-compose restart

# Check status
docker-compose ps

# Clean up
docker system prune -a
```

See [DEPLOYMENT_QUICK_REF.md](DEPLOYMENT_QUICK_REF.md) for comprehensive command reference.

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete AWS EC2 deployment guide (350+ lines)
- **[DEPLOYMENT_QUICK_REF.md](DEPLOYMENT_QUICK_REF.md)** - Quick command reference
- **[CI_CD_SETUP_SUMMARY.md](CI_CD_SETUP_SUMMARY.md)** - CI/CD pipeline overview
- **[SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md)** - Database migration guide
- **[SUPABASE_QUICK_REF.md](SUPABASE_QUICK_REF.md)** - Supabase quick reference
- **[API Docs](http://localhost:8000/docs)** - Interactive API documentation (when running)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues:** https://github.com/OriD-19/vendly_backend/issues
- **Documentation:** See docs folder
- **Email:** Contact repository owner

## 🎉 Acknowledgments

- FastAPI for the amazing framework
- Supabase for PostgreSQL hosting
- AWS for cloud services
- Docker for containerization
- GitHub Actions for CI/CD

---

**Built with ❤️ using FastAPI, Docker, and AWS**