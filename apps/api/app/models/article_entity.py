"""
models/article_entity.py — SQLAlchemy ORM model for the ArticleEntity bridge table.

Links articles to the entities discovered within them.
Each row represents one (article, entity) relationship with a relevance score
indicating how prominent the entity is in the article.

relevance_score guide:
    1.0  — entity appears in the title (highest prominence)
    0.5  — entity appears only in the body
    0.75 — entity appears in both title and body
"""

import uuid

from sqlalchemy import Column, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ArticleEntity(Base):
    __tablename__ = "article_entities"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_id = Column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    # How prominent the entity is in the article (0.0 – 1.0)
    relevance_score = Column(Float, nullable=False, default=0.5)

    __table_args__ = (
        Index("ix_article_entities_article_id", "article_id"),
        Index("ix_article_entities_entity_id", "entity_id"),
        Index("ix_article_entities_article_entity", "article_id", "entity_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ArticleEntity article={self.article_id} entity={self.entity_id} score={self.relevance_score}>"
