from typing import Annotated

from starlette.responses import RedirectResponse

from form_helper import explode_ingredient_list, get_tags, upload_recipe_img
import password_validator
import database_handler
from auth_handler import create_access_token, verify_access_token
from models import User, Recipe
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, HTTPException, Response, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

@asynccontextmanager
async def lifespan(app: FastAPI):
    database_handler.startup()
    yield

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan,
              title="Recipe App",
              version="1.0.0",
              description="A simple recipe database API with user authentication and rate limiting. For Web Engineering 2",
              docs_url=None,
              redoc_url=None,
              openapi_url=None
              )

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/recipes/index.html")
@app.get("/recipes/content.php")
@app.get("/recipes/login.php")
@app.get("/recipes/register.php")
async def render_home(request: Request):
    """
    Handles POST requests to the home page.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        TemplateResponse: Renders the home page if the user is authenticated.
            If the user is not authenticated, it redirects to the login page.
    """
    payload = verify_access_token(request)

    if not payload:
        return templates.TemplateResponse("login.jinja2", {"request": request})

    username = payload["sub"]
    return templates.TemplateResponse("home.jinja2", {"request": request, "username": username})

@app.post("/")
@app.get("/")
async def home(request: Request):
    payload = verify_access_token(request)

    if not payload:
        return RedirectResponse(url="/forbidden")

    username = payload["sub"]
    recipes = database_handler.get_recipes()
    return templates.TemplateResponse("home.jinja2", {"request": request, "username": username, "recipes": recipes})


@app.get("/forbidden")
async def forbidden(request: Request):
    """
    Renders a forbidden page when the user is not authenticated.
    Returns:
        TemplateResponse: responds with a forbidden page
    """

    return templates.TemplateResponse("forbidden.jinja2", {"request": request})


@app.get("/teapot")
async def teapot(request: Request):
    """
    Handles the GET request for the teapot endpoint.
    Returns:
        JSONResponse: Returns a 418 status code with an error message indicating that the server is a teapot.
    """
    return JSONResponse(status_code=418, content={"error": "I'm a teapot"})

@app.post("/login")
@limiter.limit("50/minute")
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
        response = RedirectResponse(url="/")
        response.set_cookie(key="access_token", value=token, httponly=True)
        return response
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

@app.get("/logout")
@limiter.limit("5/minute")
async def logout(request: Request):
    """
    Handles the GET request for logging out the user.
    Args:
        request (Request): The incoming HTTP request.
    Returns:
        TemplateResponse: Renders the login page using the Jinja2 template and deletes the access token cookie.
    """
    response = templates.TemplateResponse(name="login.jinja2", context={'request': request})
    response.delete_cookie(key="access_token")
    return response


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
         RedirectResponse:
             - Redirects the forbidden page if the user is not authenticated.
     """
    if verify_access_token(request):
        return templates.TemplateResponse(
            request=request, name="createRecipe.jinja2"
        )
    else:
        return RedirectResponse(url="/forbidden")


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
    is_public: str = Form(default=""),
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
           is_public (str): Whether the recipe is public or not.

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
        if is_public == "public":
            is_public = True
        else:
            is_public = False

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
            is_public=is_public
        )
        print(data)
        database_handler.create_recipe(recipe)
        return RedirectResponse(url="/")
    else:
        return RedirectResponse(url="/forbidden")


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
    token = verify_access_token(request)
    author = token.get("sub")
    recipe = database_handler.get_recipe(recipe_id)
    if not token:
        return RedirectResponse(url="/forbidden")
    if recipe is None:
        return templates.TemplateResponse("404.jinja2", {"request": request, "error": "Recipe not found"})
    if recipe.is_public is False and recipe.author != author:
        return RedirectResponse(url="/forbidden")
    return templates.TemplateResponse("recipe.jinja2", {"request": request, "recipe": recipe})

@app.get("/api/recipe/get-partial/{recipe_id}")
@limiter.limit("10/minute")
@limiter.limit("10/minute")
async def recipe_partial(request: Request, recipe_id: int):
    """
    Retrieves a partial view of a recipe based on its ID.
    Args:
        request (Request): The incoming HTTP request.
        recipe_id (int): The unique identifier of the recipe to retrieve.
    Returns:
        TemplateResponse: Renders a partial view of the recipe if the user is authenticated and authorized.
        JSONResponse: Returns a 401 Unauthorized response if the user is not authenticated.
        JSONResponse: Returns a 404 Not Found response if the recipe does not exist.
    """
    token = verify_access_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"Unauthorized"})
    user = token.get("sub")
    recipe = database_handler.get_recipe(recipe_id)
    # maybe here it should just return an error, instead of 404 or 401 to keep data secret from unauthorized users.
    # But I decided to keep it like this for now
    if recipe is None:
        return JSONResponse(status_code=404, content={"Recipe not found"})
    if recipe.is_public is False and recipe.author != user:
        return JSONResponse(status_code=401, content={"Unauthorized"})
    return templates.TemplateResponse("recipePartial.jinja2", {"request": request, "recipe": recipe, "user": user})

@app.get("/api/recipe/get/{recipe_id}")
async def get_recipe(request: Request, recipe_id: int):
    """
    Retrieves a recipe by its ID and returns it in JSON format.
    Args:
        request (Request): The incoming HTTP request.
        recipe_id (int): The unique identifier of the recipe to retrieve.
    Returns:
        JSONResponse: Returns the recipe in JSON format if the user is authenticated and authorized.
        JSONResponse: Returns a 401 Unauthorized response if the user is not authenticated.
        JSONResponse: Returns a 404 Not Found response if the recipe does not exist.
    """
    token = verify_access_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"Unauthorized"})
    user = token.get("sub")
    recipe = database_handler.get_recipe(recipe_id)
    if recipe is None:
        return JSONResponse(status_code=404, content={"Recipe not found"})
    if recipe.is_public is False and recipe.author != user:
        return JSONResponse(status_code=401, content={"Unauthorized"})
    return JSONResponse(status_code=200, content={"recipe": jsonable_encoder(recipe)})

@app.delete("/api/recipe/delete/{recipe_id}")
@limiter.limit("5/minute")
async def delete_recipe(request: Request, recipe_id: int):
    token = verify_access_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"Unauthorized"})
    user = token.get("sub")
    recipe = database_handler.get_recipe(recipe_id)
    if recipe is None:
        return JSONResponse(status_code=404, content={"Recipe not found"})
    if recipe.author != user:
        return JSONResponse(status_code=401, content={"Unauthorized"})
    database_handler.delete_recipe(recipe_id)
    return {200, "Recipe deleted successfully"}

@app.get("/recipe/edit/{recipe_id}")
@limiter.limit("5/minute")
async def edit_recipe(request: Request, recipe_id: int):
    token = verify_access_token(request)
    if not token:
        return RedirectResponse(url="/forbidden")

    recipe = database_handler.get_recipe(recipe_id)
    if not recipe:
        return {"Error": "Recipe not found"}
    if recipe.author != token.get("sub"):
        return RedirectResponse(url="/forbidden")

    return templates.TemplateResponse("editRecipe.jinja2", {"request": request, "recipe": recipe})

@app.post("/recipe/edit/{recipe_id}")
@limiter.limit("10/minute")
async def edit_recipe(request: Request,
                      recipe_id: int,
                      title: str = Form(...),
                      img_path: UploadFile = File(...),
                      portions: int = Form(...),
                      prep_time: int = Form(...),
                      cook_time: int = Form(...),
                      description: str = Form(...),
                      is_public: str = Form(default="")):
    token = verify_access_token(request)

    if token:
        user = token.get("sub")
        user_id = database_handler.get_user(user).id
        form_data = await request.form()
        # Extract the form data
        data = {key: value for key, value in form_data.items()}
        # Extract the ingredient and tag data
        ingredients = explode_ingredient_list(data)
        tags = get_tags(data, "tags")

        path = upload_recipe_img(img_path, title)
        original_recipe = database_handler.get_recipe(recipe_id)
        if original_recipe is None:
            return templates.TemplateResponse("404.jinja2", {"request": request, "error": "Recipe not found"})
        if original_recipe.author != user:
            return templates.TemplateResponse("forbidden.jinja2", {"request": request, "error": "You are not allowed to edit this recipe"})
        if path is None:
            path = original_recipe.img_path

        if is_public == "public":
            is_public = True
        else:
            is_public = False
        # Create a new recipe object with the updated data
        recipe = Recipe(
            title=title,
            img_path=path,
            portions=portions,
            prep_time=prep_time,
            cook_time=cook_time,
            text=description,
            ingredients=ingredients,
            tags=tags,
            author=user,
            author_id=user_id,
            is_public=is_public,
            id = original_recipe.id,
        )



        print(data)
        database_handler.update_recipe(recipe)
        return RedirectResponse(url="/")
    else:
        return RedirectResponse(url="/forbidden")

# add security layer to doc and redoc endpoints
@app.get("/docs", include_in_schema=False)
async def get_docs(request: Request):
    """
    Redirects to the Swagger UI documentation page.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        RedirectResponse: Redirects to the Swagger UI documentation page.
    """
    if not verify_access_token(request):
        return RedirectResponse(url="/forbidden")
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
@app.get("/redoc", include_in_schema=False)
async def get_redoc(request: Request):
    """
    Redirects to the ReDoc documentation page.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        RedirectResponse: Redirects to the ReDoc documentation page.
    """
    if not verify_access_token(request):
        return RedirectResponse(url="/forbidden")
    return get_redoc_html(openapi_url="/openapi.json", title="docs")

@app.get("/openapi.json", include_in_schema=False)
def get_openapi_json(request: Request):
    """
    Generates the OpenAPI schema for the application.

    Returns:
        dict: The OpenAPI schema as a dictionary.
    """
    if not verify_access_token(request):
        return RedirectResponse(url="/forbidden")
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )