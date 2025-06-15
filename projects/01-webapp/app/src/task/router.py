from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from src.task.models import TaskCreate, TaskOut
from src.database.database import azdb
from src.database.models import Task
from src.auth.utils import get_current_active_user

router = APIRouter(
    prefix="/task",
    dependencies=[Depends(get_current_active_user)]
)

@router.get("/task", response_model=List[TaskOut])
def get_task(db: Session = Depends(azdb.get_db)):
    return db.query(Task).all()

@router.post("/task", response_model=TaskOut)
def create_task(task: TaskCreate, db: Session = Depends(azdb.get_db)):
    new_task = Task(title= task.title, done = task.done)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task