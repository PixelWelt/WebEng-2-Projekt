"""
This module handles all database operations for the application.
"""
from sqlalchemy import create_engine, select
from sqlmodel import Session, SQLModel
from models import User, Recipe
from sqlalchemy.exc import SQLAlchemyError
import os

ENGINE = None


def startup():
    """Initializes the database connection and creates tables if they don't exist."""
    global ENGINE
    os.makedirs("data", exist_ok=True)
    ENGINE = create_engine("sqlite:///data/database1.sqlite")
    SQLModel.metadata.create_all(ENGINE)


# region user
def get_user(username: str) -> User | None:
    """Fetches a user from the database by username.

    Args:
        username (str): The username of the user to fetch.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    with Session(ENGINE) as session:
        query = select(User).where(User.username == username)
        fetched_user = session.exec(query).first()
        print(fetched_user)
        print(does_username_exist(username))
        if fetched_user:
            return fetched_user[0]

    return None


def create_user(user_to_create: User) -> bool:
    """Creates a new user in the database.

    Args:
        user_to_create (User): The user object to be added to the database.

    Returns:
        bool: True if the user was successfully created, False if the username already exists.
    """
    if does_username_exist(user_to_create.username):
        return False
    with Session(ENGINE) as session:
        session.add(user_to_create)
        session.commit()
    return True


def does_username_exist(username: str) -> bool:
    """Checks if a username exists in the database.

    Args:
        username (str): The username to check.

    Returns:
        bool: True if the username exists, False otherwise.
    """
    with Session(ENGINE) as session:
        query = select(User).where(User.username == username)
        fetched_user = session.exec(query).first()
        return fetched_user is not None


#endregion user

#region recipe


def create_recipe(recipe_to_create: Recipe):
    """Creates a new recipe in the database.

    Args:
        recipe_to_create (Recipe): The recipe object to be added to the database.
    """
    with Session(ENGINE) as session:
        session.add(recipe_to_create)
        session.commit()


def get_recipe(recipe_id: int) -> Recipe:
    """Fetches a recipe from the database by its ID.

    Args:
        recipe_id (int): The ID of the recipe to fetch.

    Returns:
        Recipe: The recipe object if found, otherwise None.
    """
    with Session(ENGINE) as session:
        query = select(Recipe).where(Recipe.id == recipe_id)
        fetched_recipe = session.exec(query).first()
        return fetched_recipe[0] if fetched_recipe else None

def get_recipes(start=0, amount=10) -> list[Recipe]:
    """Fetches recipes from the database with pagination.

    Args:
        start (int): The starting index.
        amount (int): The number of recipes to fetch.

    Returns:
        list[Recipe]: A list of recipe objects.
    """
    with Session(ENGINE) as session:
        query = select(Recipe).offset(start).limit(amount)
        fetched_recipes = session.exec(query).all()
        return fetched_recipes

#endregion
def delete_recipe(recipe_id):
    """Deletes a recipe from the database by its recipe ID.

    Args:
        recipe_id (int): The ID of the recipe to delete.

    Returns:
        bool: True if the recipe was successfully deleted, otherwise False.
    """
    with Session(ENGINE) as session:
        try:
            from sqlalchemy import delete
            query = delete(Recipe).where(Recipe.id == recipe_id)
            result = session.exec(query)
            session.commit()
            return True
        except SQLAlchemyError as e:
            return False



def update_recipe(recipe):
    with Session(ENGINE) as session:
        try:
            db_recipe = session.get(Recipe, recipe.id)
            if not db_recipe:
                return False
            for key, value in recipe.dict(exclude_unset=True).items():
                setattr(db_recipe, key, value)
            session.add(db_recipe)
            session.commit()
            print("Recipe updated successfully")
            return True
        except SQLAlchemyError as e:
            print(e)
            return False