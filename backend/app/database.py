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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/revenue_recovery",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
