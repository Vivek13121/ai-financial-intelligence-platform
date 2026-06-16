import sys
sys.path.insert(0, "d:\\ai sentiment analysis")

from packages.pipeline.entity_service import extract_entities

results = extract_entities(
    title="Tesla shares surge as Wall Street upgrades stock amid AI push",
    content="Tesla Inc (TSLA) saw its stock price jump 5 percent after analysts at Goldman Sachs and JPMorgan raised their price targets. CEO Elon Musk announced new AI robotics plans. The Federal Reserve kept interest rates unchanged."
)

print(f"Found {len(results)} entities:")
for r in results:
    symbol = r["symbol"] or "N/A"
    print(f"  {r['name']:30s} | {r['type']:15s} | {symbol:6s} | {r['relevance_score']:.1f}")
