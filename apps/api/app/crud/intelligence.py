from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, desc, or_, String

from app.models.article import Article
from app.models.sentiment_result import SentimentResult
from app.models.entity import Entity
from app.models.article_entity import ArticleEntity
from app.crud.analytics import get_sentiment_score
from app.schemas.intelligence import (
    CompanyIntelligence, 
    IntelligenceOverview, 
    ForecastDataPoint
)
from app.schemas.article import ArticleResponse

def resolve_entity(db: Session, search_term: str):
    """Resolve a search term to a canonical Entity using priority-ranked matching."""
    if not search_term:
        return None
    term = search_term.strip()
    term_lower = term.lower()

    # 1. Exact ticker match
    entity = db.query(Entity).filter(func.lower(Entity.symbol) == term_lower).first()
    if entity:
        return entity

    # 2. Exact alias match (JSON array containment)
    entities = db.query(Entity).filter(cast(Entity.aliases, String).ilike(f'%"{term}"%')).all()
    for ent in entities:
        if any(a.lower() == term_lower for a in ent.aliases):
            return ent

    # 3. Exact canonical name match
    entity = db.query(Entity).filter(func.lower(Entity.name) == term_lower).first()
    if entity:
        return entity

    # 4. Prefix match on name
    entity = db.query(Entity).filter(Entity.name.ilike(f"{term}%")).first()
    if entity:
        return entity

    # 5. Contains match on name
    entity = db.query(Entity).filter(Entity.name.ilike(f"%{term}%")).first()
    return entity

def get_company_intelligence(db: Session, company_name: str) -> CompanyIntelligence:
    canonical_entity = resolve_entity(db, company_name)
    resolved_name = canonical_entity.name if canonical_entity else company_name

    if canonical_entity:
        filter_cond = Article.id.in_(
            db.query(ArticleEntity.article_id).filter(ArticleEntity.entity_id == canonical_entity.id)
        )
    else:
        term = f"%{company_name}%"
        filter_cond = or_(
            Article.company.ilike(term),
            Article.title.ilike(term),
            Article.content.ilike(term)
        )

    # Deduplicate articles by URL (or ID if no URL) using a window function
    subq = (
        db.query(
            Article.id,
            func.row_number().over(
                partition_by=func.coalesce(Article.article_url, cast(Article.id, String)),
                order_by=Article.created_at.desc()
            ).label("rn")
        )
        .filter(filter_cond)
        .subquery()
    )
    
    unique_articles_filter = Article.id.in_(db.query(subq.c.id).filter(subq.c.rn == 1))
    
    # 1. Total Articles & Distribution
    articles_query = db.query(Article).filter(unique_articles_filter)
    total_articles = articles_query.count()
    
    distribution = {"positive": 0, "negative": 0, "neutral": 0}
    sentiment_counts = (
        db.query(SentimentResult.sentiment_label, func.count(SentimentResult.id))
        .join(Article, SentimentResult.article_id == Article.id)
        .filter(unique_articles_filter)
        .group_by(SentimentResult.sentiment_label)
        .all()
    )
    for label, count in sentiment_counts:
        distribution[label.lower()] = count
        
    current_sentiment = get_sentiment_score(distribution)
    
    # 2. Related News Feed
    recent_articles = (
        articles_query
        .order_by(Article.created_at.desc())
        .limit(10)
        .all()
    )
    
    # 3. Sentiment Trend (last 30 days)
    start_date = datetime.utcnow() - timedelta(days=30)
    
    daily_sentiments = (
        db.query(
            cast(SentimentResult.processed_at, Date).label("date"),
            SentimentResult.sentiment_label,
            func.count(SentimentResult.id).label("count")
        )
        .join(Article, SentimentResult.article_id == Article.id)
        .filter(unique_articles_filter)
        .filter(SentimentResult.processed_at >= start_date)
        .group_by(cast(SentimentResult.processed_at, Date), SentimentResult.sentiment_label)
        .all()
    )
    
    daily_articles = (
        db.query(
            cast(Article.created_at, Date).label("date"),
            func.count(Article.id).label("count")
        )
        .filter(unique_articles_filter)
        .filter(Article.created_at >= start_date)
        .group_by(cast(Article.created_at, Date))
        .all()
    )
    
    timeline = {}
    for row in daily_articles:
        date_str = str(row.date)
        timeline[date_str] = {
            "date": date_str, "sentiment_score": 50.0,
            "positive_count": 0, "negative_count": 0, "neutral_count": 0,
            "article_count": row.count
        }
        
    for row in daily_sentiments:
        date_str = str(row.date)
        if date_str not in timeline:
            timeline[date_str] = {
                "date": date_str, "sentiment_score": 50.0,
                "positive_count": 0, "negative_count": 0, "neutral_count": 0,
                "article_count": 0
            }
        label = row.sentiment_label.lower()
        if label == "positive": timeline[date_str]["positive_count"] += row.count
        elif label == "negative": timeline[date_str]["negative_count"] += row.count
        else: timeline[date_str]["neutral_count"] += row.count
            
    for date_str, data in timeline.items():
        data["sentiment_score"] = get_sentiment_score({
            "positive": data["positive_count"],
            "negative": data["negative_count"],
            "neutral": data["neutral_count"]
        })
        
    sorted_timeline = sorted(list(timeline.values()), key=lambda x: x["date"])
    
    # 4. Forecast Graph (Linear Trend Extrapolation)
    # We do a simple linear regression on the last 14 days of data to project the next 7 days.
    # If not enough data, we assume flat trend.
    forecast = []
    forecast_direction = "Stable"
    
    recent_14d = sorted_timeline[-14:]
    if len(recent_14d) >= 3:
        # Simple slope calculation
        y_vals = [d["sentiment_score"] for d in recent_14d]
        x_vals = list(range(len(y_vals)))
        x_mean = sum(x_vals) / len(x_vals)
        y_mean = sum(y_vals) / len(y_vals)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean)**2 for x in x_vals)
        slope = numerator / denominator if denominator != 0 else 0
        
        last_y = y_vals[-1]
        last_date = datetime.strptime(recent_14d[-1]["date"], "%Y-%m-%d")
        
        for i in range(1, 8):
            next_date = last_date + timedelta(days=i)
            # dampen the slope slightly for forecasting (mean reversion)
            predicted_y = last_y + (slope * 0.5 * i) 
            predicted_y = max(0.0, min(100.0, predicted_y)) # bound between 0 and 100
            
            forecast.append({
                "date": next_date.strftime("%Y-%m-%d"),
                "predicted_sentiment": predicted_y
            })
            
        if slope > 0.5: forecast_direction = "Bullish"
        elif slope < -0.5: forecast_direction = "Bearish"
    else:
        # Flat extrapolation if sparse data
        last_date = datetime.utcnow()
        for i in range(1, 8):
            next_date = last_date + timedelta(days=i)
            forecast.append({
                "date": next_date.strftime("%Y-%m-%d"),
                "predicted_sentiment": current_sentiment
            })
            
    # 5. AI Insight Panel (NLG)
    insights = f"Coverage for {company_name} has been sparse recently."
    if total_articles > 0:
        recent_vol = sum(d["article_count"] for d in recent_14d)
        prev_vol = total_articles - recent_vol
        
        # Calculate sentiment delta
        if len(sorted_timeline) >= 2:
            first_half = sorted_timeline[:len(sorted_timeline)//2]
            second_half = sorted_timeline[len(sorted_timeline)//2:]
            
            avg_first = sum(d["sentiment_score"] for d in first_half) / len(first_half) if first_half else 50
            avg_second = sum(d["sentiment_score"] for d in second_half) / len(second_half) if second_half else 50
            
            sentiment_improved = avg_second > (avg_first + 2)
            sentiment_declined = avg_second < (avg_first - 2)
        else:
            sentiment_improved = False
            sentiment_declined = False

        vol_trend = "increased significantly" if recent_vol > prev_vol else "remained stable"
        if recent_vol < prev_vol / 2: vol_trend = "decreased"

        if sentiment_improved:
            insights = f"Coverage {vol_trend} while sentiment improved over the recent period. The {forecast_direction.lower()} forecast is supported by {recent_vol} recent articles showing positive momentum."
        elif sentiment_declined:
            insights = f"Coverage {vol_trend} but sentiment has declined recently. A {forecast_direction.lower()} trend is emerging from the latest {recent_vol} articles."
        else:
            if current_sentiment > 60:
                insights = f"Coverage {vol_trend} and {company_name} maintains a strong positive reputation. The market mood remains bullish overall."
            elif current_sentiment < 40:
                insights = f"Coverage {vol_trend} and {company_name} continues to face negative media sentiment, remaining relatively stable at bearish levels."
            else:
                insights = f"Media coverage for {company_name} {vol_trend} and sentiment remains largely neutral over the observed period."

    # 6. Related Topics
    import re
    stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "by", "from", "and", "or", "but", "is", "are", "was", "were", "this", "that", "it"}
    topic_freq = {}
    
    for article in recent_articles:
        if article.title:
            words = re.findall(r'\b[A-Z][a-z]+\b', article.title)
            for w in words:
                w_lower = w.lower()
                if len(w) > 3 and w_lower not in stop_words and w_lower not in company_name.lower():
                    topic_freq[w] = topic_freq.get(w, 0) + 1
                    
    sorted_topics = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)
    related_topics = [t[0] for t in sorted_topics[:5]]
    if not related_topics:
        related_topics = [company_name, "Market Performance", "Earnings"]
    
    return CompanyIntelligence(
        company_name=resolved_name,
        overview=IntelligenceOverview(
            total_articles=total_articles,
            current_sentiment=current_sentiment,
            forecast_direction=forecast_direction
        ),
        news_feed=recent_articles,
        sentiment_trend=sorted_timeline,
        forecast=forecast,
        insights=insights,
        sentiment_distribution=distribution,
        related_topics=related_topics
    )

def get_search_suggestions(db: Session, query: str) -> list[str]:
    search_term = f"{query}%"

    # Query entities table — resolves by name, symbol, or aliases
    entities = (
        db.query(Entity.name, func.count(ArticleEntity.id).label("mentions"))
        .outerjoin(ArticleEntity, Entity.id == ArticleEntity.entity_id)
        .filter(or_(
            Entity.name.ilike(search_term),
            Entity.symbol.ilike(search_term),
            cast(Entity.aliases, String).ilike(f'%"{query}%')
        ))
        .group_by(Entity.name)
        .order_by(desc("mentions"))
        .limit(5)
        .all()
    )

    return [e[0] for e in entities if e[0]]
