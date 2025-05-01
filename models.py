from pydantic import BaseModel
from sqlalchemy import event
from sqlmodel import Field, SQLModel, Column, JSON
from enum import Enum
import datetime

class StepType(Enum):
    Title = 0,
    subtitle = 1,
    step = 2

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    password: str

class Step(BaseModel):
    stepType: StepType
    text: str


class Recipe(SQLModel, table=True):
    id: int| None = Field(default=None, primary_key=True)
    title: str
    img_path: str
    tags: list[str] | None = Field(default=None, sa_column=Column(JSON))
    ingredients: list[str] | None = Field(default=None, sa_column=Column(JSON))
    steps: list[Step] | None = Field(default=None, sa_column=Column(JSON))
    description: str
    author: str
    author_id: int
    created: None | datetime.datetime

@event.listens_for(Recipe,'before_insert')
def update_created_modified_on_create_listener(mapper, connection, target):
  """ Event listener that runs before a record is updated, and sets the create/modified field accordingly."""
  target.created = datetime.datetime.now()
