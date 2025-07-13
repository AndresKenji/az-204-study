from typing import Optional
from fastapi import Request

class LoginForm:
    def __init__(self, request: Request):
        self.request:Request = request
        self.username: Optional[str]
        self.password: Optional[str]

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")

