from sqlalchemy import create_engine, select
from sqlmodel import Session, SQLModel
from models import User, Recipe

engine = None


def startup():
    global engine
    engine = create_engine('sqlite:///database.sqlite')
    SQLModel.metadata.create_all(engine)

#region user
def get_user(username: str) -> User | None:
    """Fetches a user from the database by username.

    Args:
        username (str): The username of the user to fetch.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    with Session(engine) as session:
        query = select(User).where(User.username == username)
        fetched_user = session.exec(query).first()
        return fetched_user[0]


def create_user(user_to_create: User) -> bool:
    """Creates a new user in the database.

    Args:
        user_to_create (User): The user object to be added to the database.

    Returns:
        bool: True if the user was successfully created, False if the username already exists.
    """
    if does_username_exist(user_to_create.username):
        return False
    with Session(engine) as session:
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
    with Session(engine) as session:
        query = select(User).where(User.username == username)
        fetched_user = session.exec(query).first()
        return fetched_user is not None
#endregion

#region recipe

def create_recipe(recipe_to_create: Recipe):
    """Creates a new recipe in the database.

    Args:
        recipe_to_create (Recipe): The recipe object to be added to the database.
    """
    with Session(engine) as session:
        session.add(recipe_to_create)
        session.commit()


def retrieve_recipe(id: int) -> Recipe:
    """Fetches a recipe from the database by its ID.

    Args:
        id (int): The ID of the recipe to fetch.

    Returns:
        Recipe: The recipe object if found, otherwise None.
    """
    with Session(engine) as session:
        query = select(Recipe).where(Recipe.id == id)
        fetched_recipe = session.exec(query).first()
        return fetched_recipe[0]