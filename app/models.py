from sqlalchemy import event
from sqlmodel import Field, SQLModel, Column, JSON
import datetime


class User(SQLModel, table=True):
    """
    Represents a user in the database.
    Attributes:
        id (int | None): The unique identifier for the user. Primary key.
        username (str): The username of the user.
        password (str): The password of the user.
    """
    id: int | None = Field(default=None, primary_key=True)
    username: str
    password: str

class Recipe(SQLModel, table=True):
    """
    Represents a recipe in the database.

    Attributes:
        id (int | None): The unique identifier for the recipe. Primary key.
        portions (int): The number of portions the recipe serves.
        prep_time (int): The preparation time in minutes.
        cook_time (int): The cooking time in minutes.
        title (str): The title of the recipe.
        img_path (str): The file path to the recipe's image.
        tags (list[str] | None): A list of tags associated with the recipe, stored as JSON.
        ingredients (list[str] | None): A list of ingredients for the recipe, stored as JSON.
        text (str): The text description of the recipe. Created by a rich text editor.
        author (str): The name of the recipe's author.
        author_id (int): The unique identifier of the author.
        created (datetime.datetime | None): The timestamp when the recipe was created.
    """
    id: int| None = Field(default=None, primary_key=True)
    title: str
    portions: int
    prep_time: int
    cook_time: int
    img_path: str
    tags: list[str] | None = Field(default=None, sa_column=Column(JSON))
    ingredients: list[dict[str, str]] | None = Field(default=None, sa_column=Column(JSON))
    text: str
    author: str
    author_id: int
    is_public: bool = Field(default=False)
    created: None | datetime.datetime

@event.listens_for(Recipe,'before_insert')
def update_created_modified_on_create_listener(mapper, connection, target):
    """Sets the `created` timestamp before inserting a new `Recipe` record.

    This listener is triggered automatically by SQLAlchemy before a new
    `Recipe` instance is inserted into the database. It assigns the current
    datetime to the `created` field of the `Recipe` instance.

    Args:
        mapper: The SQLAlchemy mapper object.
        connection: The database connection being used.
        target: The `Recipe` instance being inserted.
    """
    target.created = datetime.datetime.now()
