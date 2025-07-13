from pydantic import BaseModel
from fastapi import Request

class TaskCreate(BaseModel):
    title: str
    description:str
    done: bool = False

    async def from_request(self, request:Request):
        form = await request.form()
        self.title = form.get("title")
        self.title = form.get("description")

class TaskOut(BaseModel):
    id: int
    title: str
    done: bool
    user_id: int

    class Config:
        from_attributes = True