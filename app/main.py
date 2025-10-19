from enum import Enum
from fastapi import FastAPI
from app.database import get_db, Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}
