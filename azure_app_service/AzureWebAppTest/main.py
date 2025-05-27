from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn


@asynccontextmanager
async def lifespan(_aplication: FastAPI) -> AsyncGenerator:
    # hacer algo al inicio de la app

    yield

    # hacer algo al final de la app


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins = ["*"],
        allow_credentials = True,
        allow_methods = ["*"],
        allow_headers= ["*"]
    )
]

app = FastAPI(
    description= "Azure Web app test api"
    , lifespan= lifespan
    ,middleware= middleware
    ,version= "0.0.1"
    ,title="AzWebTest"
)

@app.get("/")
async def root():
    return {"message":"app running"}

@app.get("/hello/{name}")
async def root(name:str = "world"):
    return {"message":f"Hello {name}"}

@app.get("/ping", include_in_schema=False)
async def ping() -> dict[str, str]:
    return {"status":"pong"}


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)