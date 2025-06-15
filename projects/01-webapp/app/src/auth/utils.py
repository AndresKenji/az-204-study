import os
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime,timedelta, timezone
from typing import Annotated
import jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status, Depends, APIRouter
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from src.database.database import azdb
from src.database.models import User as db_user
from src.auth.models import (
    User,
    UserInDB,
    TokenData
)

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str) -> User | None:
    with contextmanager(db.get_db)() as session:
        user:db_user = session.query(db_user).filter(db_user.username == username).first()
        if user is not None:
            return User(
                id= user.id,
                full_name= user.full_name,
                username= user.username,
                email= user.email,
                hashed_password= user.hased_password,
                disabled= user.disabled
            )
        else:
            return None

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(azdb, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


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
                new_user.hased_password = get_password_hash(os.getenv("admin_pwd"))
                db.add(new_user)
                db.commit()
            else:
                print("Admin user already exists")

    except Exception as e:
        print("Failed creating or checking admin user")
        raise e
    yield

