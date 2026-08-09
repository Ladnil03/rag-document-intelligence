"""Small, non-destructive schema migrations applied at startup.

These are intentionally limited to the Phase 5 ownership transition.
Anything beyond belongs in Alembic under ``backend/alembic/versions/``.
"""

from sqlalchemy import inspect, text

from app.db.base import engine


def migrate_phase5_schema() -> None:
    """Add ``documents.user_id`` + index when the column is missing.

    ``create_all`` creates the new users table but does not add a column to
    an existing documents table. Pre-authentication rows intentionally
    remain unowned (NULL user_id), so no user is ever assigned another
    person's data.
    """
    inspector = inspect(engine)
    if "documents" not in inspector.get_table_names():
        return

    document_columns = {column["name"] for column in inspector.get_columns("documents")}
    if "user_id" in document_columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE documents ADD COLUMN user_id INTEGER REFERENCES users(id)")
        )
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_documents_user_id ON documents (user_id)")
        )
