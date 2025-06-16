from datetime import date
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    id: int
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    hashed_password: str
    is_admin: bool
    creation_date: date
    disable_date: Optional[date]

    class Config:
        from_attributes = True

class CreateUser(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    plain_password: str

class UserShow(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    is_admin: bool
    creation_date: date
    disable_date: Optional[date]

    class Config:
        from_attributes = True

