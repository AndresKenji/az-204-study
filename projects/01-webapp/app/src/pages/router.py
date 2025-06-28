from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, status, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from src.auth import router as auth_routes
from src.task import router as task_routes
from src.auth import security
from src.pages.schemas import LoginForm
from src.database import azdb


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
        msg = "Incorrect Username or Password"
        return templates.TemplateResponse(
            name="login.html",
            request=request,
            context={"request":request, "msg":msg}
        )
    return response

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

        tasks = await task_routes.get_task(db=db, current_user=user)

        return templates.TemplateResponse(
            name="tasks.html",
            request=request,
            context={
                "request":request,
                "user":user,
                "tasks": tasks
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