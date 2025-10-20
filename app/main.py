from enum import Enum
from fastapi import FastAPI
import logging

# Database
from app.database import get_db, Base, engine

# Models
from app.models.user import User, Customer, StoreOwner, UserPreferences
from app.models.store import Store
from app.models.category import Category
from app.models.product import Product, Tag, ProductTag, ProductImage
from app.models.order import Order, OrderProduct
from app.models.chat_message import ChatMessage

# Routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.chat import router as chat_router
from app.api.orders import router as orders_router
from app.api.categories import router as categories_router
from app.api.store import router as store_router

# Middlewares
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.error_handling import ErrorHandlingMiddleware
from app.middleware.cors import setup_cors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="Vendly API",
    description="E-commerce platform API with JWT authentication",
    version="1.0.0"
)

# ========== Setup Middlewares ==========
# IMPORTANT: Order matters! Middleware executes bottom-to-top for requests,
# and top-to-bottom for responses.

# 1. Error handling (outermost - catches all errors)
app.add_middleware(ErrorHandlingMiddleware)

# 2. CORS (handle cross-origin requests)
setup_cors(app)

# 3. Authentication (validate JWT tokens)
app.add_middleware(AuthMiddleware)

# 4. Logging (innermost - logs all requests/responses)
app.add_middleware(LoggingMiddleware)

logger.info("Middlewares configured successfully")

# ========== Include Routers ==========
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(chat_router)
app.include_router(orders_router)
app.include_router(categories_router)
app.include_router(store_router)

logger.info("API routers registered successfully")


@app.get("/")
async def root():
    return {
        "message": "Welcome to Vendly API",
        "version": "1.0.0",
        "docs": "/docs"
    }
