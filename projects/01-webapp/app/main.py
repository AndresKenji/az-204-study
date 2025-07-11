from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.task.router import router as task_router
from src.auth.router import router as auth_router
from src.pages.router import router as pages_router
from src.database import Base, azdb
from src.auth.security import azure_scheme, LoginRedirectException
import uvicorn
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
]

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()
    yield

app = FastAPI(
    title="Todo simple app",
    description="A simple todo app using FastAPI and SQLAlchemy",
    version="0.1.0",
    middleware=middleware,
    lifespan=lifespan,
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': os.getenv("OPENAPI_CLIENT_ID"),
        'scopes': [f"api://{os.getenv('AZURE_CLIENT_ID')}/user_impersonation"]
    }
)



app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.include_router(task_router)
app.include_router(pages_router)

@app.exception_handler(LoginRedirectException)
async def login_redirect_exception_handler(request: Request, exc: LoginRedirectException):
    return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)



Base.metadata.create_all(bind=azdb.engine)

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)