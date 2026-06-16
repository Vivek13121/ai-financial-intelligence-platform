"""
worker/jobs/entity_job.py — rq job function for entity extraction.

Responsibility:
  Receive an article_id (UUID string), fetch the article from DB,
  run spaCy NER + alias normalization, and store the discovered entities
  in the entities and article_entities tables.

Design:
  - Uses packages/pipeline/entity_service.py for extraction logic.
  - Creates Entity records if they don't already exist (get-or-create pattern).
  - Creates ArticleEntity bridge records linking the article to each entity.
  - Skips articles that have already been processed (idempotent).
"""

import logging

logger = logging.getLogger(__name__)


def run_entity_job(article_id: str) -> None:
    """
    rq job function — extract entities from an article and store them.

    Args:
        article_id: UUID string of the article to process.
    """
    from app.database import SessionLocal
    from app.models.article import Article
    from app.models.entity import Entity
    from app.models.article_entity import ArticleEntity
    from packages.pipeline.entity_service import extract_entities
    from uuid import UUID

    logger.info("Starting entity extraction for article_id=%s", article_id)

    db = SessionLocal()
    try:
        # Fetch article
        article = db.query(Article).filter(Article.id == UUID(article_id)).first()
        if article is None:
            raise ValueError(
                f"entity_job: article_id={article_id!r} not found in DB."
            )

        # Check if already processed (idempotent)
        existing = db.query(ArticleEntity).filter(
            ArticleEntity.article_id == UUID(article_id)
        ).first()
        if existing:
            logger.info("Article %s already has entities extracted. Skipping.", article_id)
            return

        # Extract entities using spaCy + alias normalization
        entities = extract_entities(
            title=article.title or "",
            content=article.content or "",
        )

        if not entities:
            logger.info("No entities found in article_id=%s", article_id)
            return

        stored_count = 0
        for ent_data in entities:
            # Get or create the Entity record
            entity = db.query(Entity).filter(Entity.name == ent_data["name"]).first()

            if entity is None:
                entity = Entity(
                    name=ent_data["name"],
                    type=ent_data["type"],
                    symbol=ent_data.get("symbol"),
                    aliases=[ent_data["name"].lower()],
                )
                db.add(entity)
                db.flush()  # Get the ID without committing
                logger.debug("Created new entity: %s (%s)", ent_data["name"], ent_data["type"])

            # Create the bridge record
            article_entity = ArticleEntity(
                article_id=UUID(article_id),
                entity_id=entity.id,
                relevance_score=ent_data["relevance_score"],
            )
            db.add(article_entity)
            stored_count += 1

        db.commit()
        logger.info(
            "Extracted %d entities for article_id=%s (title: %s)",
            stored_count,
            article_id,
            (article.title or "")[:60],
        )

    except Exception as exc:
        db.rollback()
        logger.error("Entity extraction failed for article_id=%s: %s", article_id, exc)
        raise
    finally:
        db.close()
