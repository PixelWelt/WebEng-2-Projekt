from typing import Annotated

import password_validator
import database_handler
from models import User
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Body, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_handler.startup()
    yield
app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



@app.post("/login")
async def login(user: Annotated[User, Form()]):
    user.password = password_validator.Hasher.get_password_hash(user.password)
    return user

@app.post("/register")
async def login(request: Request, username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    errors = []
    if password != confirm_password:
        errors.append('Passwords do not match')



    if len(errors) != 0:
        return templates.TemplateResponse(name="login.jinja2", context={"success": False, "errors": errors, 'request': request})
    else:
        password = password_validator.Hasher.get_password_hash(password)
        user = User(username=username, password=password)
        database_handler.create_user(user)
        return templates.TemplateResponse(name="login.jinja2", context={"success": True, 'request': request})

@app.get("/login", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.jinja2"
    )


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
