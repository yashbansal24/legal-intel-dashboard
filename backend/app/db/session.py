from sqlmodel import Session
from .engine import engine

def get_session() -> Session:
    return Session(engine)