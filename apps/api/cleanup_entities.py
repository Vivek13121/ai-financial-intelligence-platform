import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../../'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models.entity import Entity
from app.models.article_entity import ArticleEntity
from app.config import settings
import spacy
from packages.pipeline.entity_service import _normalize_entity, COMPANY_ALIASES, ORGANIZATION_ALIASES, _is_valid_entity, SPACY_LABEL_MAP
import re

nlp = spacy.load("en_core_web_sm")

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

all_aliases = {**COMPANY_ALIASES, **ORGANIZATION_ALIASES}

entities = db.query(Entity).all()
print(f"Total entities before cleanup: {len(entities)}")

deleted_count = 0
merged_count = 0
renamed_count = 0

for e in entities:
    # 1. Try normalization
    normalized = _normalize_entity(e.name)
    
    canonical_name = None
    etype = None
    symbol = None

    if normalized:
        canonical_name, etype, symbol = normalized
    else:
        text_lower = e.name.lower()
        found_alias = False
        for alias_key, (acanonical, aetype, asymbol) in all_aliases.items():
            if len(alias_key) > 2 and re.search(r'\b' + re.escape(alias_key) + r'\b', text_lower):
                canonical_name = acanonical
                etype = aetype
                symbol = asymbol
                found_alias = True
                break
        
        if not found_alias:
            # Need to validate if it's a valid entity
            doc = nlp(e.name)
            ent = doc.ents[0] if len(doc.ents) > 0 else doc
            
            if not _is_valid_entity(ent):
                print(f"Deleting invalid entity: {e.name}")
                db.delete(e)
                deleted_count += 1
                continue
            else:
                canonical_name = e.name # Keep as is

    if canonical_name and canonical_name != e.name:
        # Does canonical_name exist?
        target_entity = db.query(Entity).filter(Entity.name == canonical_name).first()
        
        if not target_entity:
            print(f"Renaming '{e.name}' -> '{canonical_name}'")
            e.name = canonical_name
            if etype: e.type = etype
            if symbol: e.symbol = symbol
            renamed_count += 1
            db.flush()
            continue
        
        target_id = target_entity.id
        if e.id == target_id:
            continue
            
        print(f"Merging '{e.name}' into '{canonical_name}'")
        # Re-link ArticleEntities
        aes = db.query(ArticleEntity).filter(ArticleEntity.entity_id == e.id).all()
        for ae in aes:
            existing_ae = db.query(ArticleEntity).filter(
                ArticleEntity.article_id == ae.article_id,
                ArticleEntity.entity_id == target_id
            ).first()
            if existing_ae:
                existing_ae.relevance_score = max(existing_ae.relevance_score, ae.relevance_score)
                db.delete(ae)
            else:
                ae.entity_id = target_id
        
        db.delete(e)
        merged_count += 1

db.commit()

entities_after = db.query(Entity).count()
print(f"--- CLEANUP COMPLETE ---")
print(f"Total entities after cleanup: {entities_after}")
print(f"Deleted invalid entities: {deleted_count}")
print(f"Merged duplicate entities: {merged_count}")
print(f"Renamed entities to canonical: {renamed_count}")
