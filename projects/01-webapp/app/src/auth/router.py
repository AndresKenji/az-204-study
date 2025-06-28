from typing import Annotated, List, Optional
from datetime import timedelta, datetime
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
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
    get_current_user_from_cookie,
    check_admin
    )
from src.auth.dependencies import check_admin_user

class LoginForm:
    def __init__(self, request: Request):
        self.request:Request = request
        self.username: Optional[str]
        self.password: Optional[str]

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")

templates = Jinja2Templates(directory="templates")

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

@router.post("/token-cookie")
async def login_for_access_token_cookie(response: Response,form_data: OAuth2PasswordRequestForm= Depends()):
    user = authenticate_user(azdb, form_data.username, form_data.password)
    if not user:
        print(f"No se encontro el usuario {form_data.username} en la base de datos")
        return False
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id}, expires_delta=access_token_expires
    )

    response.set_cookie(key='access_token', value=access_token, httponly=True)

    return True

# endpoints para el login por html
@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request":request}
    )

@router.post("/", response_class=HTMLResponse)
async def login(request: Request):
    form = LoginForm(request)
    await form.create_oauth_form()
    response = RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)

    validate_user_cookie = await login_for_access_token_cookie(response= response, form_data=form)

    if not validate_user_cookie:
        msg = "Incorrect Username or Password"
        return templates.TemplateResponse(
            name="login.html",
            request=request,
            context={"request":request, "msg":msg}
        )
    return response


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