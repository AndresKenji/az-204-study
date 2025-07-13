from sqlalchemy.orm import Session

from fastapi import APIRouter, Request, status, Depends, Security
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from src.auth import router as auth_routes
from src.auth import security
from src.auth.middlewares import get_current_user_from_request, require_authenticated_user
from src.task import task, schemas
from src.pages.schemas import LoginForm
from src.database import azdb
from datetime import timedelta, datetime
import os
import requests



router = APIRouter(
    tags=["pages"],
    responses={404: {"description": "Not found"}},
    include_in_schema=False
)

templates = Jinja2Templates(directory="templates")

# Importar los archivos de rutas para que se registren automáticamente
from src.pages.routes import auth
from src.pages.routes import tasks

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = get_current_user_from_request(request)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "user": user,
            "is_authenticated": user is not None
        }
    )




