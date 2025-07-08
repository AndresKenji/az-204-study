from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, status, Depends, Security
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from src.auth import router as auth_routes
from src.task import task
from src.auth import security
from src.auth.models import User
from src.pages.schemas import LoginForm
from src.database import azdb
from src.auth.security import azure_scheme
import os


router = APIRouter(
    tags=["pages"],
    responses={404: {"description": "Not found"}},
    include_in_schema=False
)

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context= {"r":request}
        )

# endpoints para el login por html
@router.get("/auth", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request":request}
    )

@router.post("/auth", response_class=HTMLResponse)
async def login(request: Request):
    form = LoginForm(request)
    await form.create_oauth_form()
    response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)

    validate_user_cookie = await auth_routes.login_for_access_token_cookie(response= response, form_data=form)

    if not validate_user_cookie:

        return templates.TemplateResponse(
            name="login.html",
            request=request,
            context={"request":request,
                     "msg":"Incorrect Username or Password",
                     "error":True
                     }
        )
    return response

####################### LOGIN POR AZURE ##############################
from fastapi.responses import RedirectResponse
import os
from urllib.parse import urlencode

@router.get("/login/azure")
async def login_azure():
    # Define una URI de redirección absoluta completa
    redirect_uri = "http://localhost:8000/auth/callback"

    params = {
        "client_id": os.getenv("APP_CLIENT_ID"),  # Cambiado de CLIENT_ID a APP_CLIENT_ID para coincidir con tus variables
        "response_type": "code",
        "redirect_uri": redirect_uri,  # URI absoluta
        "response_mode": "query",
        "scope": "openid profile email",
        "state": "/profile"  # Guardar la ruta a la que redirigir después
    }
    url = (
        f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}/oauth2/v2.0/authorize?"
        + urlencode(params)
    )
    return RedirectResponse(url)

@router.get("/auth/callback", name="azure_callback")
async def azure_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None,
):
    """Maneja el callback de Azure AD después de la autenticación."""
    if error:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": True, "msg": error_description}
        )

    try:
        # Intercambia el código de autorización por un token
        token = await azure_scheme.get_access_token(
            code=code,
            redirect_uri=str(request.url_for("azure_callback"))
        )

        # Obtén información del usuario del token
        user_info = await azure_scheme.get_user_info(token)

        # Establece una cookie con el token de acceso
        response = RedirectResponse(url=state or "/profile")
        response.set_cookie(
            key="azure_token",
            value=token.access_token,
            httponly=True,
            max_age=3600,
            secure=False  # Cambiar a True en producción
        )

        return response
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": True, "msg": str(e)}
        )

@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = RedirectResponse(url="/auth")
    # Eliminar cookies locales
    response.delete_cookie("access_token")

    # Para logout completo de Azure AD, deberías redirigir a la URL de logout de Azure
    # Esto depende de tu configuración de Azure AD
    azure_logout_url = f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}/oauth2/v2.0/logout"
    return RedirectResponse(url=azure_logout_url)


# endpoints de tareas
@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request, user: User = Security(azure_scheme), db: Session = Depends(azdb.get_db)):
    try:
        # Como ya tenemos el usuario de Azure, podemos usarlo directamente
        # Aquí necesitarías adaptar para obtener o crear un usuario local asociado a este usuario de Azure
        local_user = await security.get_or_create_local_user_from_azure(user, db)

        tasks = await task.get_task(db=db, current_user=local_user)

        return templates.TemplateResponse(
            name="tasks.html",
            request=request,
            context={
                "request": request,
                "user": user,  # Usuario de Azure
                "tasks": [t for t in tasks if not t.done],
                "completed_tasks": [t for t in tasks if t.done]
            }
        )

    except Exception as e:
        response = templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "msg": str(e),
                "error": True
            }
        )
        return response

@router.post("/tasks/done/{id}", response_class=HTMLResponse)
async def complete_task(request:Request, id: int, db:Session = Depends(azdb.get_db)):
    try:
        user = await security.get_current_user_from_cookie(request)
        if user is None:
            return RedirectResponse(url="/auth", status_code=status.HTTP_301_MOVED_PERMANENTLY)

        done = await task.complete_task(id, db, user)

        if done:
            return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)

    except Exception as e:
        response = templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "msg":e,
                "error":True
                }
            )
        response.delete_cookie("access_token")
        return response


@router.post("/tasks/delete/{id}", response_class=HTMLResponse)
async def delete_task(request:Request, id:int, db:Session = Depends(azdb.get_db)):
    try:
        user = await security.get_current_user_from_cookie(request)
        if user is None:
            return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

        if await task.delete_task(id, db, user):
            print("Tarea borrada")
            return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        response = templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "msg":e,
                "error":True
                }
            )
        response.delete_cookie("access_token")
        return response

@router.get("/tasks/create", response_class=HTMLResponse)
async def create_task_form(request:Request):
    try:
        user = await security.get_current_user_from_cookie(request)
        if user is None:
            return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

        return templates.TemplateResponse(
            request=request,
            name="create-task.html",
            context={
                "user": user,
            }
        )

    except Exception as e:
        response = templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "msg":e,
                "error":True
                }
            )
        response.delete_cookie("access_token")
        return response


from fastapi import Security
from fastapi_azure_auth.user import User

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, db: Session = Depends(azdb.get_db)):
    """Muestra la página de perfil del usuario autenticado."""
    try:
        # Obtener el token de la cookie
        token = request.cookies.get("azure_token")
        if not token:
            return RedirectResponse(url="/login/azure")

        # Validar el token
        user_info = await azure_scheme.validate_token(token)
        if not user_info:
            return RedirectResponse(url="/login/azure")

        # Aquí puedes obtener o crear un usuario local si es necesario
        local_user = await security.get_or_create_local_user_from_azure(user_info, db)

        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": user_info,
                "local_user": local_user
            }
        )
    except Exception as e:
        response = RedirectResponse(url="/auth")
        response.delete_cookie("azure_token")
        return response






