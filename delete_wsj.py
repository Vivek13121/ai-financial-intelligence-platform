from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:vivek1312@localhost:5432/market_intelligence')

with engine.connect() as conn:
    # Delete WSJ and Reuters
    conn.execute(text("DELETE FROM articles WHERE source ILIKE '%WSJ%'"))
    conn.execute(text("DELETE FROM articles WHERE source ILIKE '%Reuters%'"))
    conn.commit()
    print("Deleted stale WSJ and Reuters articles.")

    # Check entities
    result = conn.execute(text("""
        SELECT a.id, a.title, e.name, e.type 
        FROM articles a 
        JOIN article_entities ae ON a.id = ae.article_id 
        JOIN entities e ON e.id = ae.entity_id 
        WHERE a.source = 'TheStreet' 
        LIMIT 5
    """)).fetchall()

    if result:
        print("\nEntities successfully extracted from TheStreet:")
        for r in result:
            print(f" - {r.name} ({r.type})")
    else:
        print("\nNo entities extracted yet for TheStreet. The worker might still be processing.")
