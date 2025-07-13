from pydantic import BaseModel, ValidationError
from fastapi import Request

class TaskCreate(BaseModel):
    title: str
    description: str
    done: bool = False

    @classmethod
    async def from_request(cls, request: Request):
        form = await request.form()
        title = form.get("title", "").strip()
        description = form.get("description", "").strip()

        if not title:
            raise ValidationError("El título no puede estar vacío.")

        return cls(title=title, description=description, done=False)


class TaskOut(BaseModel):
    id: int
    title: str
    done: bool
    user_id: int

    class Config:
        from_attributes = True