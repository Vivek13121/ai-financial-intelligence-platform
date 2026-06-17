import sys
import os

# Add the project root to the python path
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('apps/api'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.entity import Entity

DATABASE_URL = "postgresql://postgres:vivek1312@localhost:5432/market_intelligence"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

targets = ["Nvidia", "Apple", "Alphabet", "Google", "NetEase", "Microsoft", "NVDA", "AAPL", "GOOG", "GOOGL", "NTES", "MSFT"]

print("--- ENTITIES IN DB ---")
try:
    all_entities = db.query(Entity).all()
    for e in all_entities:
        # Check if this entity matches any of our targets
        name_lower = e.name.lower()
        aliases_lower = [a.lower() for a in (e.aliases or [])]
        symbol = e.symbol
        
        match = False
        for t in targets:
            tl = t.lower()
            if tl in name_lower or tl in aliases_lower or (symbol and tl == symbol.lower()):
                match = True
                break
                
        if match:
            print(f"ID: {e.id} | Name: {e.name} | Symbol: {e.symbol} | Aliases: {e.aliases}")

    print("\n--- ALL UNIQUE ENTITIES BY NAME ---")
    names = [e.name for e in all_entities]
    from collections import Counter
    counts = Counter(names)
    duplicates = {k: v for k, v in counts.items() if v > 1}
    if duplicates:
        print("Duplicates found:")
        for k, v in duplicates.items():
            print(f"  {k}: {v}")
    else:
        print("No duplicates by name.")
except Exception as e:
    print(f"Error querying DB: {e}")
