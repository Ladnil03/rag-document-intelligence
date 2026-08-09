from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import config  # single source of truth for DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(config.DATABASE_URL)

# Create SessionLocal class for session management
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
