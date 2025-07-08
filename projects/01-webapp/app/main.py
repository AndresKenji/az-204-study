from fastapi import FastAPI, Security, Request, Response
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.task.router import router as task_router
from src.auth.router import router as auth_router
from src.pages.router import router as pages_router
from src.database import Base, azdb
from src.auth.security import azure_scheme
import uvicorn
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator


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
    lifespan=lifespan,  # Asegurar que se usa el lifespan para cargar OpenID config
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': os.getenv("OPENAPI_CLIENT_ID"),
        'scopes': [f"api://{os.getenv('app_client_id')}/user_impersonation"]
    }
)

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse

class AzureAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Rutas excluidas de la autenticación
        excluded_paths = ["/auth", "/login/azure", "/static", "/docs", "/openapi.json", "/redoc"]

        # Verificar si la ruta actual está excluida
        path = request.url.path
        if any(path.startswith(excluded) for excluded in excluded_paths):
            # Permitir acceso sin autenticación para rutas excluidas
            return await call_next(request)

        try:
            # Intentar verificar token de Azure
            # Esto es simplificado, puedes necesitar ajustarlo según tu implementación
            token = request.cookies.get("azure_token")
            if not token:
                # Si no hay token, redirigir a login
                return RedirectResponse(url="/login/azure", status_code=302)

            # Continuar con la solicitud si el token es válido
            response = await call_next(request)
            return response

        except Exception:
            # En caso de error, redirigir a login
            return RedirectResponse(url="/auth", status_code=302)

# Agregar el middleware a la aplicación
app.add_middleware(AzureAuthMiddleware)


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.include_router(task_router)
app.include_router(pages_router)

@app.get("/az", dependencies=[Security(azure_scheme)])
async def azure_test():
    return {"message":"Hello "}


Base.metadata.create_all(bind=azdb.engine)

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)