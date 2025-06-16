import os
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime

from fastapi import APIRouter
from src.auth.security import get_password_hash
from src.auth.models import User as db_user
from src.database import azdb


@asynccontextmanager
async def check_admin_user(app: APIRouter):
    try:
        with contextmanager(azdb.get_db)() as db:
            print("Checking for admin user in db")
            admin_user = db.query(db_user).filter(db_user.username == "administrator").first()
            if admin_user is None:
                new_user = db_user()
                new_user.username = "administrator"
                new_user.full_name = "administrator local"
                new_user.email = "administrator@dblocal.com"
                new_user.hashed_password = get_password_hash(os.getenv("admin_pwd"))
                new_user.is_admin = True
                new_user.creation_date = datetime.now().date()
                db.add(new_user)
                db.commit()
            else:
                print("Admin user already exists")

    except Exception as e:
        print("Failed creating or checking admin user")
        raise e
    yield