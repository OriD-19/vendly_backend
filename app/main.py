from enum import Enum
from fastapi import FastAPI
from app.database import get_db, Base, engine
from app.models.user import User, Customer, StoreOwner, UserPreferences
from app.models.store import Store
from app.models.category import Category
from app.models.product import Product, Tag, ProductTag, ProductImage
from app.models.order import Order, OrderProduct

# Import routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vendly API",
    description="E-commerce platform API with JWT authentication",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Vendly API",
        "version": "1.0.0",
        "docs": "/docs"
    }
