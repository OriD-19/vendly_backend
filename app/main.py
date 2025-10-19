from enum import Enum
from fastapi import FastAPI
from app.database import get_db, Base, engine
from app.models.user import User, Customer, StoreOwner, UserPreferences
from app.models.store import Store
from app.models.category import Category
from app.models.product import Product, Tag, ProductTag, ProductImage
from app.models.order import Order, OrderProduct

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}
