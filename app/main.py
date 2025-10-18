from enum import Enum
from fastapi import FastAPI

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    
    if model_name is ModelName.resnet:
        return {"model_name": model_name, "message": "Residuals are cool!"}
    
    return {"model_name": model_name, "message": "LeNet is the best!"}

@app.get("/files/{file_path:path}")
async def get_file(file_path: str):
    return {"file_path": file_path, "message": "File found!"}