from contextlib import contextmanager
import os
from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from src.auth.models import User as db_user
from src.auth.schemas import User,TokenData
from src.database import azdb
from sqlalchemy.orm import Session


SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

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
                hashed_password= user.hashed_password,
                disabled= user.disabled,
                creation_date=user.creation_date,
                is_admin=user.is_admin,
                disable_date=user.disable_date
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

def check_admin(user:db_user):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No cuentas con permisos para realizar esta acción"
        )

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

async def get_current_user_from_cookie(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            logout(request)
        user = get_user(azdb, username=username)
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="error getting user")

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)],):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=os.getenv("APP_CLIENT_ID", os.getenv("app_client_id")),  # Intenta ambos nombres
    tenant_id=os.getenv("TENANT_ID", os.getenv("app_directory_id")),  # Intenta ambos nombres
    scopes={"user_impersonation": "User impersonation"},
    auto_error=False  # Importante: evita el error automático para poder manejar la redirección
)

async def get_or_create_local_user_from_azure(azure_user: User, db: Session) -> db_user:
    """Obtiene o crea un usuario local basado en el usuario de Azure AD"""

    # Buscar el usuario por email
    local_user = db.query(db_user).filter(db_user.email == azure_user.email).first()

    if not local_user:
        # Si no existe, crear un nuevo usuario
        local_user = db_user(
            username=azure_user.email,  # Usar el email como username
            email=azure_user.email,
            full_name=azure_user.name,
            hashed_password=get_password_hash("azure_user"),  # Contraseña aleatoria que no se usará
            is_admin=False,  # Por defecto no es admin
            creation_date=datetime.now().date(),
            disabled=False
        )
        db.add(local_user)
        db.commit()
        db.refresh(local_user)

    return local_user