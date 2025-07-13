from sqlalchemy.orm import Session

from fastapi import Request, status, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import ValidationError

from src.pages.router import router, templates
from src.auth import security
from src.task import task, schemas
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
            name="home.html",
            context={
                "user":user,
                }
            )
        response.set_cookie(key="error_msg",
                                value=str(e),
                                httponly=True,
                                max_age=60
                                )
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
            response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="msg",
                                value="Tarea completada exitosamente!",
                                httponly=True,
                                max_age=60
                                )
            return response
        else:
            response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="error_msg",
                                value="No se pudo completar la tarea",
                                httponly=True,
                                max_age=60
                                )
            return response

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
async def delete_task(request:Request,
                      id:int,
                      db:Session = Depends(azdb.get_db),
                     user = Depends(security.require_login)):
    try:
        if await task.delete_task(id, db, user):
            response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="msg",
                                value="Tarea eliminada exitosamente!",
                                httponly=True,
                                max_age=60
                                )
            return response
        else:
            response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="error_msg",
                                value="No se pudo eliminar la tarea",
                                httponly=True,
                                max_age=60
                                )
            return response
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

@router.post("/tasks/create", response_class=HTMLResponse)
async def create_task_from_modal(request:Request,
                                 db:Session = Depends(azdb.get_db),
                                user = Depends(security.require_login)):
    try:
        new_task_data = await schemas.TaskCreate.from_request(request)
        new_task = await task.create_task(new_task_data, db, user)
        if new_task:
            response = RedirectResponse(url="/tasks",
                                    status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="msg",
                                value="Tarea creada exitosamente!",
                                httponly=True,
                                max_age=60
                                )
            return response
        else:
            response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="error_msg",
                                value="Error al crear la tarea",
                                httponly=True,
                                max_age=60
                                )
            return response
    except ValidationError as e:
        response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="error_msg",
                            value=str(e),
                            httponly=True,
                            max_age=60
                            )
        return response
    except Exception as e:
        response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="error_msg",
                            value="Error inesperado al crear la tarea",
                            httponly=True,
                            max_age=60
                            )
        return response



