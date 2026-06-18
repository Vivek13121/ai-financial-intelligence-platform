from app.database import SessionLocal
from app.models.entity import Entity
db = SessionLocal()
jpm = db.query(Entity).filter(Entity.name == "JPMorgan Chase").first()
if jpm:
    new_aliases = list(set(jpm.aliases + ["jpmorgan", "jp morgan", "jpmorgan chase & co.", "jpmc"]))
    jpm.aliases = new_aliases
    db.commit()
    print("Updated JPM aliases:", jpm.aliases)
else:
    print("JPMorgan Chase not found")
