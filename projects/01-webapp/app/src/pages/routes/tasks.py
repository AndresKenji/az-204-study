from sqlalchemy.orm import Session

from fastapi import Request, status, Depends
from fastapi.responses import RedirectResponse, HTMLResponse

from src.pages.router import router, templates
from src.auth import security
from src.task import task
from src.database import azdb


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request:Request,
                     db:Session = Depends(azdb.get_db),
                     user = Depends(security.require_login)
                     ):
    try:
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
async def complete_task(request:Request,
                        id: int,
                        db:Session = Depends(azdb.get_db),
                     user = Depends(security.require_login)
                     ):
    try:

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
async def delete_task(request:Request, id:int, db:Session = Depends(azdb.get_db),
                     user = Depends(security.require_login)):
    try:
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
async def create_task_form(request:Request,
                     user = Depends(security.require_login)):
    try:

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
