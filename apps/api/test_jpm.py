from app.database import SessionLocal
from app.models.entity import Entity
db = SessionLocal()
for e in db.query(Entity).filter(Entity.name.ilike('%JP%')).all():
    print(f"Name: {e.name}, Symbol: {e.symbol}, Aliases: {e.aliases}")
