"""
models/entity.py — SQLAlchemy ORM model for the Entity table.

Stores unique, normalized entities (companies, people, topics, etc.)
that are extracted from financial news articles by the NLP pipeline.

Each entity has a canonical name and a type. The `aliases` JSON column
stores alternative names that all resolve to this entity (e.g., "AAPL",
"Apple Inc.", "Mac maker" all map to the entity "Apple").
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Entity(Base):
    __tablename__ = "entities"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    # Canonical name: "Apple", "Elon Musk", "Federal Reserve", "Inflation"
    name = Column(String(512), nullable=False, unique=True)
    # Type: COMPANY, PERSON, ORGANIZATION, TOPIC
    type = Column(String(64), nullable=False, default="COMPANY")
    # Ticker symbol (nullable — only for companies with stock symbols)
    symbol = Column(String(16), nullable=True)
    # JSON array of alias strings for this entity
    # e.g. ["AAPL", "Apple Inc.", "Apple Computer"]
    aliases = Column(JSONB, nullable=False, default=list)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_entities_name", "name"),
        Index("ix_entities_type", "type"),
    )

    def __repr__(self) -> str:
        return f"<Entity id={self.id} name={self.name!r} type={self.type!r}>"
