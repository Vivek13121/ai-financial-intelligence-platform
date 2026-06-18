from app.database import SessionLocal
from app.crud.intelligence import get_company_intelligence
db = SessionLocal()
names = ["JPMorgan", "JP Morgan", "JPMorgan Chase", "JPMorgan Chase & Co.", "JPMC"]
for n in names:
    data = get_company_intelligence(db, n)
    print(f"Searched: {n} -> Resolved: {data.company_name}, Articles: {data.overview.total_articles}")
