"""SQLAlchemy engine, session factory, and the declarative ``Base``.

The base is split out so models can import from it without pulling in
the rest of the application (useful for Alembic and tests).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core import config

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> tuple[bool, str]:
    """Check database connectivity for readiness and health probes."""
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            connection.execute(text("SELECT 1"))
        return True, "Database connection healthy"
    except Exception as exc:
        return False, f"Database connection failed: {str(exc)}"
