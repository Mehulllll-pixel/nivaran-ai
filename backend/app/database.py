"""
Database connection setup.

For local dev, point DATABASE_URL at a local Postgres instance, e.g.:
    postgresql://postgres:postgres@localhost:5432/revenue_recovery

If you don't want to install Postgres locally while prototyping, you can
swap this to SQLite for a day by changing DATABASE_URL to:
    sqlite:///./dev.db
(SQLAlchemy syntax stays the same either way — just remove
`connect_args` handling below if you do that.)
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
