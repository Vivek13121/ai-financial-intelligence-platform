from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re

from app.models.article import Article
from app.models.sentiment_result import SentimentResult
from app.models.forecast_result import ForecastResult

ENTITY_PATTERN = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9&.-]+|[A-Z]{2,})(?:\s+(?:[A-Z][A-Za-z0-9&.-]+|[A-Z]{2,}))*\b"
)

ENTITY_STOP_WORDS = {
    "A", "An", "And", "As", "At", "By", "For", "From", "How", "In", "Is",
    "It", "New", "Of", "On", "Or", "The", "This", "To", "With", "Why",
    "Market", "Markets", "News", "Stock", "Stocks", "Shares", "Update",
    "Breaking", "Today", "Wall Street", "Dow Jones", "Nasdaq", "S&P",
    "Reuters", "Bloomberg", "CNBC", "Yahoo Finance",
    "AI", "Buy", "Sell", "Hold", "Strong Buy", "One", "Inc", "Corp",
    "Corporation", "Company", "Ltd", "LLC", "PLC", "Monday", "Tuesday",
    "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
}

GENERIC_TOPIC_WORDS = {
    "best", "cheap", "stocks", "stock", "shares", "buy", "sell", "hold",
    "beginner", "beginners", "retirement", "dividend", "dividends", "income",
    "growth", "value", "ceo", "cfo", "analyst", "analysts", "market",
    "markets", "earnings", "options", "portfolio", "watchlist", "lifts",
    "raises", "cuts", "pt", "target", "rating",
}

ORGANIZATION_TERMS = {
    "bank", "group", "holdings", "capital", "financial", "finance",
    "technologies", "technology", "systems", "semiconductor",
    "semiconductors", "therapeutics", "pharma", "biotech", "energy",
    "motors", "airlines", "resources", "partners",
}

KNOWN_COMPANY_ALIASES = {
    "Apple": ("Apple", "AAPL"),
    "Microsoft": ("Microsoft", "MSFT"),
    "Nvidia": ("Nvidia", "NVDA"),
    "Tesla": ("Tesla", "TSLA"),
    "Amazon": ("Amazon", "AMZN"),
    "Alphabet": ("Alphabet", "Google", "GOOGL", "GOOG"),
    "Meta": ("Meta", "Facebook", "META"),
    "Netflix": ("Netflix", "NFLX"),
    "Intel": ("Intel", "INTC"),
    "AMD": ("AMD", "Advanced Micro Devices"),
    "Broadcom": ("Broadcom", "AVGO"),
    "Oracle": ("Oracle", "ORCL"),
    "Salesforce": ("Salesforce", "CRM"),
    "Adobe": ("Adobe", "ADBE"),
    "IBM": ("IBM",),
    "JPMorgan Chase": ("JPMorgan", "JPMorgan Chase", "JPM"),
    "Bank of America": ("Bank of America", "BAC"),
    "Goldman Sachs": ("Goldman Sachs", "GS"),
    "Morgan Stanley": ("Morgan Stanley", "MS"),
    "Walmart": ("Walmart", "WMT"),
    "Target": ("Target", "TGT"),
    "Costco": ("Costco", "COST"),
    "Disney": ("Disney", "DIS"),
    "Boeing": ("Boeing", "BA"),
    "Ford": ("Ford", "F"),
    "General Motors": ("General Motors", "GM"),
    "Exxon Mobil": ("Exxon", "Exxon Mobil", "XOM"),
    "Chevron": ("Chevron", "CVX"),
    "Pfizer": ("Pfizer", "PFE"),
    "Moderna": ("Moderna", "MRNA"),
    "Eli Lilly": ("Eli Lilly", "LLY"),
    "Novo Nordisk": ("Novo Nordisk", "NVO"),
    "Palantir": ("Palantir", "PLTR"),
    "Coinbase": ("Coinbase", "COIN"),
    "Block": ("Block", "Square", "SQ"),
    "PayPal": ("PayPal", "PYPL"),
}


def extract_title_entities(title: str | None) -> list[str]:
    """
    Temporary headline entity extractor for dashboard mentions.
    Replace this helper when the dedicated NER/entity pipeline lands.
    """
    if not title:
        return []

    entities = []
    seen = set()
    title_lower = title.lower()

    for canonical, aliases in KNOWN_COMPANY_ALIASES.items():
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias.lower())}\b", title_lower):
                entities.append(canonical)
                seen.add(canonical)
                break

    for match in ENTITY_PATTERN.findall(title):
        entity = match.strip(" .,-:;()[]{}")
        if not entity or entity in ENTITY_STOP_WORDS:
            continue
        if " " not in entity:
            continue
        if any(word.lower() in GENERIC_TOPIC_WORDS for word in entity.split()):
            continue
        if any(canonical in entity and canonical != entity for canonical in seen):
            continue
        if not any(word.lower() in ORGANIZATION_TERMS for word in entity.split()):
            continue
        if len(entity) <= 2 and not entity.isupper():
            continue
        if entity not in seen:
            entities.append(entity)
            seen.add(entity)
    return entities


def get_sentiment_score(distribution) -> float:
    total = distribution["positive"] + distribution["negative"] + distribution["neutral"]
    if total == 0:
        return 50.0
    score_val = ((distribution["positive"] * 1) + (distribution["negative"] * -1)) / total
    return (score_val + 1) * 50


def get_trending_companies(db: Session, start_time: datetime, recent_start: datetime):
    articles = (
        db.query(Article.id, Article.title, Article.company)
        .filter(
            (
                (Article.published_at != None) &
                (Article.published_at >= start_time)
            ) |
            (
                (Article.published_at == None) &
                (Article.created_at >= start_time)
            )
        )
        .all()
    )

    mentions = Counter()
    article_ids_by_entity = defaultdict(set)
    for article_id, title, company in articles:
        candidates = []
        if company:
            candidates.append(company)
        candidates.extend(extract_title_entities(title))

        for entity in dict.fromkeys(candidates):
            mentions[entity] += 1
            article_ids_by_entity[entity].add(article_id)

    trending_companies = []
    for company, count in mentions.most_common(5):
        article_ids = list(article_ids_by_entity[company])
        company_recent_sentiments = (
            db.query(SentimentResult.sentiment_label)
            .filter(SentimentResult.article_id.in_(article_ids))
            .filter(SentimentResult.processed_at >= recent_start)
            .all()
        )
        c_recent_dist = {"positive": 0, "negative": 0, "neutral": 0}
        for (label,) in company_recent_sentiments:
            if label.lower() in c_recent_dist:
                c_recent_dist[label.lower()] += 1
        c_recent_score = get_sentiment_score(c_recent_dist)

        company_past_sentiments = (
            db.query(SentimentResult.sentiment_label)
            .filter(SentimentResult.article_id.in_(article_ids))
            .filter(SentimentResult.processed_at >= start_time)
            .filter(SentimentResult.processed_at < recent_start)
            .all()
        )
        c_past_dist = {"positive": 0, "negative": 0, "neutral": 0}
        for (label,) in company_past_sentiments:
            if label.lower() in c_past_dist:
                c_past_dist[label.lower()] += 1
        c_past_score = get_sentiment_score(c_past_dist) if company_past_sentiments else 50.0

        direction = "flat"
        if c_recent_score > c_past_score + 2:
            direction = "up"
        elif c_recent_score < c_past_score - 2:
            direction = "down"

        latest_sentiment = "neutral"
        if c_recent_score > 60:
            latest_sentiment = "positive"
        elif c_recent_score < 40:
            latest_sentiment = "negative"

        trending_companies.append({
            "company": company,
            "mentions": count,
            "sentiment": latest_sentiment,
            "direction": direction
        })

    return trending_companies

def get_stats(db: Session):
    now = datetime.utcnow()
    
    # Fallback hierarchy: 7d -> 14d -> 30d
    window_days = 7
    for days in [7, 14, 30]:
        start = now - timedelta(days=days)
        count = db.query(SentimentResult).filter(SentimentResult.processed_at >= start).count()
        if count > 0:
            window_days = days
            break
            
    window_used = f"{window_days}d"
    
    if window_days == 7:
        recent_days = 3
    elif window_days == 14:
        recent_days = 7
    else:
        recent_days = 15

    recent_start = now - timedelta(days=recent_days)
    previous_start = now - timedelta(days=window_days)
    
    total_articles = db.query(Article).count()
    total_forecasts = db.query(ForecastResult).count()
    last_24h_start = now - timedelta(hours=24)
    articles_today = db.query(Article).filter(Article.created_at >= last_24h_start).count()
    
    # Get recent window score and distribution
    recent_counts = (
        db.query(SentimentResult.sentiment_label, func.count(SentimentResult.id))
        .filter(SentimentResult.processed_at >= recent_start)
        .group_by(SentimentResult.sentiment_label)
        .all()
    )
    recent_dist = {"positive": 0, "negative": 0, "neutral": 0}
    for label, count in recent_counts:
        if label.lower() in recent_dist:
            recent_dist[label.lower()] = count
            
    recent_score = get_sentiment_score(recent_dist)
    
    # Get previous window score
    previous_counts = (
        db.query(SentimentResult.sentiment_label, func.count(SentimentResult.id))
        .filter(SentimentResult.processed_at >= previous_start)
        .filter(SentimentResult.processed_at < recent_start)
        .group_by(SentimentResult.sentiment_label)
        .all()
    )
    previous_dist = {"positive": 0, "negative": 0, "neutral": 0}
    for label, count in previous_counts:
        if label.lower() in previous_dist:
            previous_dist[label.lower()] = count
            
    previous_score = get_sentiment_score(previous_dist)
    
    # Calculate whole window distribution
    whole_window_dist = {
        "positive": recent_dist["positive"] + previous_dist["positive"],
        "negative": recent_dist["negative"] + previous_dist["negative"],
        "neutral": recent_dist["neutral"] + previous_dist["neutral"]
    }

    sentiment_change = 0.0
    if sum(previous_dist.values()) > 0 and sum(recent_dist.values()) > 0:
        sentiment_change = recent_score - previous_score
        
    market_mood = "Neutral"
    if recent_score > 60:
        market_mood = "Bullish"
    elif recent_score < 40:
        market_mood = "Bearish"

    mood_change = sentiment_change 

    trending_companies = get_trending_companies(
        db=db,
        start_time=now - timedelta(days=7),
        recent_start=recent_start,
    )

    return {
        "window_used": window_used,
        "total_articles": total_articles,
        "total_forecasts": total_forecasts,
        "market_sentiment_score": round(recent_score, 1),
        "sentiment_distribution": whole_window_dist,
        "market_mood": market_mood,
        "mood_change": round(mood_change, 1),
        "articles_today": articles_today,
        "sentiment_change": round(sentiment_change, 1),
        "trending_companies": trending_companies
    }

def get_activity_feed(db: Session, limit: int = 10):
    events = []
    
    # Recent articles
    articles = db.query(Article).order_by(Article.created_at.desc()).limit(limit).all()
    for a in articles:
        events.append({
            "id": f"art-{a.id}",
            "timestamp": a.created_at,
            "type": "article_ingested",
            "message": f"New article processed: {a.title[:60]}..."
        })
        
    # Recent sentiment
    sentiments = db.query(SentimentResult).join(Article).order_by(SentimentResult.processed_at.desc()).limit(limit).all()
    for s in sentiments:
        events.append({
            "id": f"sen-{s.id}",
            "timestamp": s.processed_at,
            "type": "sentiment_generated",
            "message": f"Sentiment ({s.sentiment_label}) generated for article."
        })
        
    # Recent forecasts
    forecasts = db.query(ForecastResult).order_by(ForecastResult.generated_at.desc()).limit(limit).all()
    for f in forecasts:
        events.append({
            "id": f"for-{f.id}",
            "timestamp": f.generated_at,
            "type": "forecast_completed",
            "message": f"Forecast generated for {f.forecast_date.strftime('%Y-%m-%d')}."
        })
        
    events.sort(key=lambda x: x["timestamp"], reverse=True)
    return events[:limit]

def get_timeseries(db: Session, days: int = 30):
    """
    Returns daily aggregated data for the past `days` days.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # We'll use SQLAlchemy's func.date() to truncate to daily buckets.
    # Note: func.cast(Column, Date) also works well in PostgreSQL.
    from sqlalchemy import Date, cast
    
    # 1. Aggregate sentiments
    daily_sentiments = (
        db.query(
            cast(SentimentResult.processed_at, Date).label("date"),
            SentimentResult.sentiment_label,
            func.count(SentimentResult.id).label("count")
        )
        .filter(SentimentResult.processed_at >= start_date)
        .group_by(cast(SentimentResult.processed_at, Date), SentimentResult.sentiment_label)
        .all()
    )
    
    # 2. Aggregate article volume
    daily_articles = (
        db.query(
            cast(Article.created_at, Date).label("date"),
            func.count(Article.id).label("count")
        )
        .filter(Article.created_at >= start_date)
        .group_by(cast(Article.created_at, Date))
        .all()
    )
    
    # 3. Combine into a timeline
    timeline = {}
    
    for row in daily_articles:
        date_str = str(row.date)
        timeline[date_str] = {
            "date": date_str,
            "sentiment_score": 50.0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "article_count": row.count
        }
        
    for row in daily_sentiments:
        date_str = str(row.date)
        if date_str not in timeline:
            timeline[date_str] = {
                "date": date_str,
                "sentiment_score": 50.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "article_count": 0
            }
        
        label = row.sentiment_label.lower()
        if label == "positive":
            timeline[date_str]["positive_count"] += row.count
        elif label == "negative":
            timeline[date_str]["negative_count"] += row.count
        else:
            timeline[date_str]["neutral_count"] += row.count
            
    # Calculate scores
    for date_str, data in timeline.items():
        data["sentiment_score"] = get_sentiment_score({
            "positive": data["positive_count"],
            "negative": data["negative_count"],
            "neutral": data["neutral_count"]
        })
        
    # Sort chronologically
    sorted_timeline = sorted(list(timeline.values()), key=lambda x: x["date"])
    return sorted_timeline

def get_topics(db: Session, days: int = 7):
    """
    Returns top positive and negative topics based on average sentiment score.
    Uses the new Entity Intelligence Layer.
    """
    from app.models.entity import Entity
    from app.models.article_entity import ArticleEntity
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    records = (
        db.query(
            Entity.name,
            Entity.type,
            SentimentResult.sentiment_label
        )
        .join(ArticleEntity, ArticleEntity.entity_id == Entity.id)
        .join(SentimentResult, SentimentResult.article_id == ArticleEntity.article_id)
        .filter(SentimentResult.processed_at >= start_date)
        .filter(Entity.type.in_(["COMPANY", "TOPIC", "INDUSTRY", "ORGANIZATION"]))
        .all()
    )
    
    # Exclude generic verbs, adjectives, stopwords, days of week, months, and single-word sentiment terms
    exclude_words = {
        "today", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
        "january", "february", "march", "april", "june", "july", "august", "september", "october", "november", "december",
        "falls", "rises", "hard", "pressure", "carnage", "signs", "soars", "plummets", "surges", "drops",
        "good", "bad", "great", "terrible", "bullish", "bearish", "high", "low", "up", "down",
        "stock", "stocks", "market", "markets", "shares", "investors", "wall street", "dow", "nasdaq",
        "report", "earnings", "quarter", "revenue", "profit", "loss", "buy", "sell", "hold"
    }
    
    topics_map = {}
    
    for entity_name, entity_type, label in records:
        if not entity_name: 
            continue
            
        t_lower = entity_name.lower().strip()
        if len(t_lower) <= 2 or t_lower in exclude_words: 
            continue
        
        if entity_name not in topics_map:
            topics_map[entity_name] = {"positive": 0, "negative": 0, "neutral": 0, "mentions": 0}
        topics_map[entity_name][label.lower()] += 1
        topics_map[entity_name]["mentions"] += 1

    results = []
    for topic, data in topics_map.items():
        score = get_sentiment_score(data)
        results.append({
            "topic": topic,
            "mentions": data["mentions"],
            "sentiment_score": score
        })
        
    results.sort(key=lambda x: x["sentiment_score"], reverse=True)
    
    # Dynamic Threshold filtering to avoid empty states
    thresholds = [3, 2, 1]
    filtered_results = []
    
    for th in thresholds:
        filtered = [r for r in results if r["mentions"] >= th]
        if len(filtered) >= 4:
            filtered_results = filtered
            break
            
    if not filtered_results:
        filtered_results = results

    # We use strict > 50 and < 50 for bullish and bearish to avoid completely neutral topics
    positive_topics = [r for r in filtered_results if r["sentiment_score"] > 50]
    negative_topics = [r for r in filtered_results if r["sentiment_score"] < 50]
    
    positive_topics.sort(key=lambda x: (x["sentiment_score"], x["mentions"]), reverse=True)
    negative_topics.sort(key=lambda x: (x["sentiment_score"], -x["mentions"])) # Lowest score first, highest mentions tiebreaker

    return {
        "positive": positive_topics[:10],
        "negative": negative_topics[:10]
    }
