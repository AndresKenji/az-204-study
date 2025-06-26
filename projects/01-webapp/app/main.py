from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.task.router import router as task_router
from src.auth.router import router as auth_router
from src.database import Base, azdb
import uvicorn


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins = ["*"],
        allow_credentials = True,
        allow_methods = ["*"],
        allow_headers= ["*"]
    )
]
app = FastAPI(
    title="Todo simple app",
    description="A simple todo app using FastAPI and SQLAlchemy",
    version="0.1.0",
    middleware=middleware
)

app.include_router(auth_router)
app.include_router(task_router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context= {"r":request}
        )

Base.metadata.create_all(bind=azdb.engine)

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)