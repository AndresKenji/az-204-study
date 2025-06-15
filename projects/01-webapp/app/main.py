from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from src.task.router import router as task_router
from src.auth.router import router as auth_router
import uvicorn


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
    title="Todo simple app",
    description="A simple todo app using FastAPI and SQLAlchemy",
    version="0.1.0",
    middleware=middleware
)

app.include_router(auth_router)
app.include_router(task_router)


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)