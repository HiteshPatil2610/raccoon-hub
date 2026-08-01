"""
database.py
------------------------------------------------------------------
SQLAlchemy engine/session setup for the Postgres database on Render.
------------------------------------------------------------------
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# `pool_pre_ping` avoids "server closed the connection unexpectedly"
# errors that are common with free-tier managed Postgres instances
# that idle-timeout connections.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session, rolls back on error, always closes it."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()