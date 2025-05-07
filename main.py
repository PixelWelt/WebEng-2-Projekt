from typing import Annotated
from form_helper import explode_ingredient_list, get_tags, upload_recipe_img
import password_validator
import database_handler
from auth_handler import create_access_token, verify_access_token
from models import User, Recipe
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, HTTPException, Response, File, UploadFile, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_handler.startup()
    yield

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan, title="Recipe DB")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



@app.post("/login")
@limiter.limit("5/minute")
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
    errors = []
    if user.password == "" or user.username == "":
        errors.append("Username or password cannot be empty")
        return templates.TemplateResponse(name="login.jinja2", context={"success": False, "errors": errors, 'request': request})
    verification_user = database_handler.get_user(user.username)
    if verification_user is None:
        errors.append("User does not exist")
        return templates.TemplateResponse(name="login.jinja2", context={"success": False, "errors": errors, 'request': request})
    if password_validator.Hasher.verify_password(user.password, verification_user.password):
        token = create_access_token({"sub": user.username})
        response.set_cookie(key="access_token", value=token, httponly=True)
        return {"success": True, "message": "Login successful"}
    elif database_handler.get_user(user.username) is None:
        errors.append("User does not exist")
    else:
        errors.append("Invalid credentials")

    return templates.TemplateResponse(name="login.jinja2", context={"success": False, "errors": errors, 'request': request})

@app.get("/login", response_class=HTMLResponse)
@limiter.limit("5/minute")
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
@limiter.limit("5/minute")
async def get_login_state(request: Request):
    """
        Checks if the user is logged in by verifying the access token.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            dict: A dictionary indicating the login state.
                - If the user is logged in: The result of `verify_access_token(request)`.
                - If an error occurs: {"success": False, "message": <error_message>}.
    """
    try:
        return verify_access_token(request)
    except HTTPException as e:
        return {"success": False, "message": str(e.detail)}
    except Exception:
        return {"success": False, "message": "An unexpected error occurred"}

@app.post("/register")
@limiter.limit("5/minute")
async def login(request: Request, username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    errors = []
    if password == "" or username == "" or confirm_password == "":
        errors.append("Username or password cannot be empty")
        return templates.TemplateResponse(name="login.jinja2",
                                          context={"success": False, "errors": errors, 'request': request})
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
@limiter.limit("10/minute")
async def add_recipe(request: Request):
    """
     Handles the GET request for the recipe creation page.

     Args:
         request (Request): The incoming HTTP request.

     Returns:
         TemplateResponse:
             - Renders the recipe creation page if the user is authenticated.
             - Renders the forbidden page if the user is not authenticated.
     """
    if verify_access_token(request):
        return templates.TemplateResponse(
            request=request, name="createRecipe.jinja2"
        )
    else:
        return templates.TemplateResponse("forbidden.jinja2", {"request": request})


@app.post("/recipe/add")
@limiter.limit("5/minute")
async def add_recipe(
    request: Request,
    title: str = Form(...),
    img_path: UploadFile = File(...),
    portions: int = Form(...),
    prep_time: int = Form(...),
    cook_time: int = Form(...),
    description: str = Form(...),
):
    """
       Handles the POST request for adding a new recipe.

       Args:
           request (Request): The incoming HTTP request.
           title (str): The title of the recipe.
           img_path (UploadFile): The uploaded image file for the recipe.
           portions (int): The number of portions the recipe serves.
           prep_time (int): The preparation time in minutes.
           cook_time (int): The cooking time in minutes.
           description (str): A description or instructions for the recipe.

       Returns:
           TemplateResponse:
               - Renders the recipe page if the recipe is successfully created.
               - Renders the forbidden page if the user is not authenticated.
               - Renders the recipe creation page with errors if the image upload fails.
       """
    token = verify_access_token(request)

    if token:
        author = token.get("sub")
        user_id = database_handler.get_user(author).id
        form_data = await request.form()
        # Extract the form data
        data = {key: value for key, value in form_data.items()}
        # Extract the ingredient and tag data
        ingredients = explode_ingredient_list(data)
        tags = get_tags(data, "tags")

        path = upload_recipe_img(img_path, title)

        if path is None:
            errors = ["Invalid image file or file exceeds 10MB"]
            return templates.TemplateResponse("createRecipe.jinja2", {"request": request, "errors": errors})

        recipe = Recipe(
            title=title,
            img_path=path,
            portions=portions,
            prep_time=prep_time,
            cook_time=cook_time,
            text=description,
            ingredients=ingredients,
            tags=tags,
            author=author,
            author_id=user_id,
        )
        print(data)
        database_handler.create_recipe(recipe)
        return templates.TemplateResponse("recipe.jinja2", {"request": request, "recipe": recipe})
    else:
        return templates.TemplateResponse("forbidden.jinja2", {"request": request})


@app.get("/recipe/view/{recipe_id}")
@limiter.limit("5/minute")
async def view_recipe(request: Request, recipe_id: int):
    """
    Retrieves and displays a recipe based on its ID.

    Args:
        request (Request): The incoming HTTP request.
        recipe_id (int): The unique identifier of the recipe to retrieve.

    Returns:
        TemplateResponse: Renders the recipe page if the recipe is found.
        TemplateResponse: Returns an 404 page if the recipe is not found.
    """
    recipe = database_handler.retrieve_recipe(recipe_id)
    if recipe is None:
        return {"Error": "Recipe not found"}
    return templates.TemplateResponse("recipe.jinja2", {"request": request, "recipe": recipe})
