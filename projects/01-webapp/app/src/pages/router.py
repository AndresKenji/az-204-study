from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, status, Depends, Security
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from src.auth import router as auth_routes
from src.task import task
from src.auth import security
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

# endpoints de tareas
@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request:Request, db:Session = Depends(azdb.get_db)):
    try:
        user = await security.get_current_user_from_cookie(request)
        if user is None:
            RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

        tasks = await task.get_task(db=db, current_user=user)

        return templates.TemplateResponse(
            name="tasks.html",
            request=request,
            context={
                "request":request,
                "user":user,
                "tasks": [t for t in tasks if not t.done],
                "completed_tasks": [t for t in tasks if t.done]
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


# Ruta para autenticación con Azure Entra ID
@router.get("/login-azure", response_class=HTMLResponse)
async def login_azure(request: Request):
    """
    Página para iniciar el flujo de autenticación con Azure Entra ID.
    """
    # Construir manualmente la URL de autorización de Azure AD
    client_id = os.getenv("AZURE_CLIENT_ID")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    redirect_uri = os.getenv("AZURE_REDIRECT_URI", "http://localhost:8000/auth/callback")

    # URL de autorización de Azure AD OAuth 2.0
    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"

    # Parámetros requeridos para la autenticación
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": "openid profile email User.Read",
        "state": "12345"  # Debería ser un valor aleatorio para evitar CSRF
    }

    # Construir la URL completa con los parámetros
    auth_url_with_params = f"{auth_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"

    return RedirectResponse(url=auth_url_with_params, status_code=status.HTTP_302_FOUND)

@router.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(request: Request, code: str = None, state: str = None, error: str = None, db: Session = Depends(azdb.get_db)):
    """
    Callback para la autenticación con Azure Entra ID.
    """
    if error:
        return templates.TemplateResponse(
            name="login.html",
            request=request,
            context={"request": request, "msg": f"Error: {error}", "error": True}
        )

    try:
        if not code:
            return templates.TemplateResponse(
                name="login.html",
                request=request,
                context={"request": request, "msg": "No se recibió código de autorización", "error": True}
            )

        # Intercambiar el código por un token de acceso
        import requests

        client_id = os.getenv("AZURE_CLIENT_ID")
        tenant_id = os.getenv("AZURE_TENANT_ID")
        redirect_uri = os.getenv("AZURE_REDIRECT_URI", "http://localhost:8000/auth/callback")

        # URL para intercambiar el código por un token
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        # Parámetros para la solicitud de token
        token_data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "scope": "openid profile email User.Read",
            "code": code,
            "redirect_uri": redirect_uri
        }

        # Solicitud para obtener el token
        token_response = requests.post(token_url, data=token_data)
        token_result = token_response.json()

        if "access_token" in token_result:
            # Obtener información del usuario con el token
            user_info_url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {token_result['access_token']}"}
            user_response = requests.get(user_info_url, headers=headers)
            user_info = user_response.json()

            if "error" in user_info:
                return templates.TemplateResponse(
                    name="login.html",
                    request=request,
                    context={"request": request, "msg": f"Error al obtener información del usuario: {user_info['error']['message']}", "error": True}
                )

            # Crear o recuperar el usuario en la base de datos
            with db:
                # Verificar si el usuario existe por email
                user_db = db.query(security.db_user).filter(security.db_user.email == user_info.get("mail") or user_info.get("userPrincipalName")).first()

                if not user_db:
                    # Crear nuevo usuario
                    user_db = security.db_user()
                    user_db.username = user_info.get("userPrincipalName", "").split('@')[0] or user_info.get("displayName", "").replace(" ", "").lower()
                    user_db.email = user_info.get("mail") or user_info.get("userPrincipalName")
                    user_db.full_name = user_info.get("displayName")
                    user_db.hashed_password = security.get_password_hash(f"azure_{user_info.get('id')}")
                    user_db.disabled = False
                    user_db.is_admin = False
                    user_db.creation_date = datetime.now().date()

                    db.add(user_db)
                    db.commit()
                    db.refresh(user_db)

            # Crear token JWT para la sesión
            access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = security.create_access_token(
                data={"sub": user_db.username, "id": user_db.id}, expires_delta=access_token_expires
            )

            # Establecer cookie y redirigir a la página de tareas
            response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key='access_token', value=access_token, httponly=True)

            return response
        else:
            error_msg = token_result.get("error_description", "Error desconocido al obtener el token")
            return templates.TemplateResponse(
                name="login.html",
                request=request,
                context={"request": request, "msg": error_msg, "error": True}
            )
    except Exception as e:
        return templates.TemplateResponse(
            name="login.html",
            request=request,
            context={"request": request, "msg": f"Error: {str(e)}", "error": True}
        )

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """
    Página de perfil del usuario
    """
    try:
        user = await security.get_current_user_from_cookie(request)
        if user is None:
            return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

        return templates.TemplateResponse(
            name="profile.html",
            request=request,
            context={"request": request, "user": user}
        )
    except Exception as e:
        response = templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "msg": f"Error: {str(e)}",
                "error": True
            }
        )
        response.delete_cookie("access_token")
        return response

@router.get("/logout", response_class=HTMLResponse)
async def logout_page(request: Request):
    """
    Logout del usuario
    """
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response






