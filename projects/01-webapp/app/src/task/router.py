from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from typing import List
from sqlalchemy.orm import Session
from src.task.schemas import TaskCreate, TaskOut
from src.database import azdb
from src.task.models import Task
from src.auth.security import get_current_active_user
from src.auth.models import User
from src import exceptions
from src.task.task import (
    get_task,
    complete_task,
    update_task,
    delete_task,
    create_task
)

router = APIRouter(
    prefix="/api/task",
    tags=["Tasks"]
    # dependencies=[Depends(get_current_active_user)]
)

@router.get("/", response_model=List[TaskOut])
async def get_task_(db: Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    try:
         return await get_task(db,current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e

@router.get("/done/{id}",response_model=TaskOut)
async def complete_task_(id:int, db:Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    try:
        if await complete_task(id,db,current_user):
            return Response(status_code=status.HTTP_200_OK, content="ok")
    except exceptions.TaskNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e
    except exceptions.UserNotOwner as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not the owner of the resource"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e

@router.post("/", response_model=TaskOut)
async def create_task_(task: TaskCreate, db: Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    try:
        return await create_task(task, db, current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e

@router.put("/{id}", response_model=TaskOut)
async def update_task_(id:int,data: TaskCreate, db: Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    try:
        return await update_task(id,data, db, current_user)
    except exceptions.TaskNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except exceptions.UserNotOwner as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


@router.delete("/{id}")
async def delete_task_(id:int,db: Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    try:
        if await delete_task(id, db, current_user):
            return Response(status_code=status.HTTP_204_NO_CONTENT,content="Task deleted")
    except exceptions.TaskNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except exceptions.UserNotOwner as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e
