from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:vivek1312@localhost:5432/market_intelligence')
with engine.connect() as conn:
    conn.execute(text("DELETE FROM articles WHERE source IN ('WSJ Markets', 'Reuters', 'Reuters Business')"))
    conn.commit()
print("Deleted stale articles")
