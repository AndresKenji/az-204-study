from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, status, Depends, Security
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from src.auth import router as auth_routes
from src.task import task
from src.auth import security
from src.pages.schemas import LoginForm
from src.database import azdb
from src.auth.security import azure_scheme



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
@router.get("/login/azure")
async def login_azure():
    # Redirige al usuario al login de Azure AD
    return RedirectResponse(url="/profile")

@router.get("/logout", response_class=HTMLResponse)
async def logout(request:Request):
    response = templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "msg":"Logout Successful"
        }
    )
    response.delete_cookie("access_token")
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


from fastapi import Security
from fastapi_azure_auth.user import User

@router.get("/profile")
async def profile(user: User = Security(azure_scheme)):
    return {"name": user.name, "email": user.email}






