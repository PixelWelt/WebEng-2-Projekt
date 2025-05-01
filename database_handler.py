from sqlalchemy import create_engine
from sqlmodel import Session
from models import User, Recipe

engine = None


def startup():
    global engine
    engine = create_engine('sqlite:///database.sqlite')

def get_user(username: str):
    pass

def create_user(user: User):
    with Session(engine) as session:
        session.add(user)
        session.commit()

def does_user_exist(user:User) -> bool:
    pass