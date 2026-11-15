from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import DATABASE_URL


# SQLite needs this option for FastAPI's request handling.
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)


# Each request can create its own database session.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Base class for our SQLAlchemy models.
class Base(DeclarativeBase):
    pass


# FastAPI dependency: creates and closes a session per request.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()