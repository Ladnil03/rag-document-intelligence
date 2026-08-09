"""User ORM model.

Single source of truth for the `users` table. The other entity modules
import the relationship-side helpers from here.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    documents = relationship("Document", back_populates="owner")
    conversations = relationship(
        "Conversation", back_populates="owner", cascade="all, delete-orphan"
    )
