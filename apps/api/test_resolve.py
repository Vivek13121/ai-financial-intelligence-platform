from app.database import SessionLocal
from app.models.entity import Entity
from sqlalchemy import func, cast, String
db = SessionLocal()
search_term = "JPMorgan"
term_lower = search_term.lower()
e = db.query(Entity).filter(func.lower(Entity.symbol) == term_lower).first()
if e: print("Found ticker:", e.name)
entities = db.query(Entity).filter(cast(Entity.aliases, String).ilike(f'%"{search_term}"%')).all()
found_alias = None
for ent in entities:
    if any(a.lower() == term_lower for a in ent.aliases):
        found_alias = ent
        break
if found_alias: print("Found alias:", found_alias.name)
e = db.query(Entity).filter(func.lower(Entity.name) == term_lower).first()
if e: print("Found canonical:", e.name)
print("Done")
