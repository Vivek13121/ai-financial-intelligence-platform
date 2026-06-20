from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://postgres:vivek1312@localhost:5432/market_intelligence"
)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            source,
            COUNT(*) AS total_articles,
            MAX(published_at) AS latest_article
        FROM articles
        GROUP BY source
        ORDER BY total_articles DESC;
    """))

    print("\n=== NEWS SOURCE HEALTH ===\n")

    for row in result:
        print(row)