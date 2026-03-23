from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.settings import get_settings

settings = get_settings()

# Using classic psycopg2 driver for widest compatibility.
engine = create_engine(settings.postgres_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
