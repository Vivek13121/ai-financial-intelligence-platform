from app.database import SessionLocal
from app.models.entity import Entity
db = SessionLocal()
print([e.name for e in db.query(Entity).filter(Entity.name.ilike('%JP%')).all()])
print([e.name for e in db.query(Entity).all()])
