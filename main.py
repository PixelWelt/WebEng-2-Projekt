from typing import Annotated, List
from form_helper import explode_ingredient_list, explode_form_list
import password_validator
import database_handler
from auth_handler import create_access_token, verify_access_token
from models import User, Recipe
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Body, Form, HTTPException, Response, File, UploadFile
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
async def login(request: Request, response: Response, user: Annotated[User, Form()]):
    """Handles user login by verifying credentials and generating an access token.

    Args:
        request (Request): The incoming HTTP request.
        response (Response): The HTTP response object to set cookies.
        user (Annotated[User, Form()]): The user object containing the username and password.

    Returns:
        dict: A dictionary containing the success status and a message.
            - If login is successful: {"success": True, "message": "Login successful"}.
            - If login fails: {"success": False, "message": "Invalid credentials"}.
    """
    verification_user = database_handler.get_user(user.username)
    if password_validator.Hasher.verify_password(user.password, verification_user.password):
        token = create_access_token({"sub": user.username})
        response.set_cookie(key="access_token", value=token, httponly=True)
        return {"success": True, "message": "Login successful"}
    else:
        errors = ["Invalid credentials"]
        return templates.TemplateResponse(name="login.jinja2", context={"success": False, "errors": errors, 'request': request})

@app.get("/login", response_class=HTMLResponse)
async def root(request: Request):
    """
    Handles the GET request for the login page.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        TemplateResponse: Renders the login page using the Jinja2 template.
    """
    return templates.TemplateResponse(
        request=request, name="login.jinja2"
    )

@app.get("/get_login_state")
async def get_login_state(request: Request):
    try:
        return verify_access_token(request)
    except HTTPException as e:
        return {"success": False, "message": str(e.detail)}
    except Exception:
        return {"success": False, "message": "An unexpected error occurred"}

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


@app.get("/recipe/add")
async def add_recipe(request: Request):
    if verify_access_token(request):
        return templates.TemplateResponse(
            request=request, name="createRecipe.jinja2"
        )
    else:
        return {"Error": "You are not logged in"}
@app.post("/recipe/add")
async def add_recipe(
    request: Request,
    title: str = Form(...),
    img_path: UploadFile = File(...),
    portions: int = Form(...),
    prep_time: int = Form(...),
    cook_time: int = Form(...),
    description: str = Form(...),
):
    if verify_access_token(request):
        form_data = await request.form()
        data = {key: value for key, value in form_data.items()}
        ingredients = explode_ingredient_list(data)
        tags = explode_form_list(data, "tags")
        recipe = Recipe(
            title=title,
            img_path=img_path.filename,
            portions=portions,
            prep_time=prep_time,
            cook_time=cook_time,
            text=description,
            ingredients=ingredients,
            tags=tags,
        )

        return {"success": True, "data": recipe}
    else:
        return {"Error": "You are not logged in"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
