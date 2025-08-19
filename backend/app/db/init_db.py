from sqlmodel import SQLModel
from .engine import engine

def init_db() -> None:
    SQLModel.metadata.create_all(engine)
