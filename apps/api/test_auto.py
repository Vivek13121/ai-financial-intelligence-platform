from app.database import SessionLocal
from app.crud.intelligence import get_search_suggestions
db = SessionLocal()
print("Search JPM:", get_search_suggestions(db, "JPM"))
print("Search JP Morgan:", get_search_suggestions(db, "JP Morgan"))
