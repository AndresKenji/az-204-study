from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from typing import List
from sqlalchemy.orm import Session
from src.task.schemas import TaskCreate, TaskOut
from src.database import azdb
from src.task.models import Task
from src.auth.security import get_current_active_user
from src.auth.models import User
from src import exeptions

router = APIRouter(
    prefix="/api/task",
    tags=["Tasks"]
    # dependencies=[Depends(get_current_active_user)]
)

@router.get("/", response_model=List[TaskOut])
async def get_task(db: Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    try:
        if current_user.username == "administrator":
            return db.query(Task).all()
        return db.query(Task).filter(Task.user_id == current_user.id).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e

@router.get("/done/{id}",response_model=TaskOut)
async def complete_task(id:int, db:Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    task = db.query(Task).filter(Task.id == id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if current_user.is_admin or current_user.id == task.user_id:
        task.done = True
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not the owner of the resource"
        )

@router.post("/", response_model=TaskOut)
async def create_task(task: TaskCreate, db: Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    new_task = Task(title= task.title, done = task.done, user_id = current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.put("/{id}", response_model=TaskOut)
async def update_task(id:int,data: TaskCreate, db: Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    task = db.query(Task).filter(Task.id == id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if current_user.id != task.user_id or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not the owner of the resource"
        )

    task.done = data.done
    task.title = data.title
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{id}")
async def delete_task(id:int,db: Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    task = db.query(Task).filter(Task.id == id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if current_user.id != task.user_id or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not the owner of the resource"
        )
    db.delete(task)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT, content="ok")
