from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    done: bool = False

class TaskOut(BaseModel):
    id: int
    title: str
    done: bool

    class Config:
        from_attributes = True