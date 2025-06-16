from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from src.task.schemas import TaskCreate, TaskOut
from src.database import azdb
from src.task.models import Task
from src.auth.security import get_current_active_user
from src.auth.models import User

router = APIRouter(
    prefix="/task",
    # dependencies=[Depends(get_current_active_user)]
)

@router.get("/task", response_model=List[TaskOut])
def get_task(db: Session = Depends(azdb.get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.username == "administrator":
        return db.query(Task).all()
    return db.query(Task).filter(Task.user_id == current_user.id).all()

@router.post("/task", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(azdb.get_db)):
    new_task = Task(title= task.title, done = task.done)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task