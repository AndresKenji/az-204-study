from typing import Annotated,List
from datetime import timedelta, datetime
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.auth.schemas import Token, User, UserShow, CreateUser
from src.auth.models import User as db_user
from src.database import azdb
from src.auth.security import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user,
    check_admin
    )
from src.auth.dependencies import check_admin_user


router = APIRouter(
    prefix="/auth",
    lifespan=check_admin_user
)

@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],) -> Token:
    user = authenticate_user(azdb, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me/", response_model=UserShow)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

@router.get("/users/", response_model=List[UserShow])
async def read_users_me(db:Session= Depends(azdb.get_db),current_user: db_user = Depends(get_current_active_user)):
    check_admin(current_user)
    return db.query(db_user).all()


@router.get("/users/me/items/")
async def read_own_items(current_user: Annotated[User, Depends(get_current_active_user)]):
    return [{"item_id": "Foo", "owner": current_user.username}]

@router.get("/users/disable/{user_id}", description="Deshabilita o Habilita un usuario")
async def disable_enable_user(user_id:int, db:Session= Depends(azdb.get_db), current_user: db_user = Depends(get_current_active_user)):
    check_admin(current_user)
    user = db.query(db_user).filter(db_user.id == user_id).first()
    if user:
        user.disabled = not user.disabled
        user.disable_date = datetime.now().date()
        db.add(user)
        db.commit()
        return "ok"
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontro al usuario")


@router.post("/users", response_model=User, description="Creates a user")
async def create_user(userdata: CreateUser, db: Session = Depends(azdb.get_db)):
    existing_user = db.query(db_user).filter(db_user.email == userdata.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    new_user = db_user()
    new_user.username = userdata.username
    new_user.full_name = userdata.full_name
    new_user.email = userdata.email
    new_user.hashed_password = get_password_hash(userdata.plain_password)
    new_user.creation_date = datetime.now().date()

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user