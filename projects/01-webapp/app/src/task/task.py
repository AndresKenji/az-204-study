from typing import List
from sqlalchemy.orm import Session
from src.auth.models import User
from src.task.models import Task
from src.task.schemas import TaskCreate, TaskOut
from src import exceptions

async def get_task(db: Session, current_user: User) -> List[Task]:
    if current_user.is_admin:
        return db.query(Task).all()
    return db.query(Task).filter(Task.user_id == current_user.id).all()


async def complete_task(id:int, db:Session, current_user: User) -> bool:
    task = db.query(Task).filter(Task.id == id).first()
    if task is None:
        raise exceptions.TaskNotFound()

    if current_user.is_admin or current_user.id == task.user_id:
        task.done = not task.done
        db.add(task)
        db.commit()
        db.refresh(task)

        return True
    else:
        raise exceptions.UserNotOwner()

async def create_task(task: TaskCreate, db: Session, current_user: User) -> Task:
    new_task = Task(title= task.title,
                    description= task.description,
                    done = task.done,
                    user_id = current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

async def update_task(id:int,data: TaskCreate, db: Session , current_user: User) -> Task:
    task = db.query(Task).filter(Task.id == id).first()
    if task is None:
        raise exceptions.TaskNotFound()

    if current_user.id != task.user_id and not current_user.is_admin:
        raise exceptions.UserNotOwner()

    task.done = data.done
    task.title = data.title
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

async def delete_task(id:int,db: Session , current_user: User) -> bool:
    task = db.query(Task).filter(Task.id == id).first()
    if task is None:
        raise exceptions.TaskNotFound()

    if current_user.id != task.user_id and not current_user.is_admin:
        raise exceptions.UserNotOwner()

    db.delete(task)
    db.commit()

    return True