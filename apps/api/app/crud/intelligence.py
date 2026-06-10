from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, desc, or_, String

from app.models.article import Article
from app.models.sentiment_result import SentimentResult
from app.crud.analytics import get_sentiment_score
from app.schemas.intelligence import (
    CompanyIntelligence, 
    IntelligenceOverview, 
    ForecastDataPoint
)
from app.schemas.article import ArticleResponse

def get_company_intelligence(db: Session, company_name: str) -> CompanyIntelligence:
    COMPANY_ALIASES = {
        "google": ["google", "alphabet", "goog", "googl"],
        "apple": ["apple", "aapl"],
        "tesla": ["tesla", "tsla"],
        "microsoft": ["microsoft", "msft"],
        "amazon": ["amazon", "amzn"],
        "nvidia": ["nvidia", "nvda"],
        "meta": ["meta", "facebook", "fb"]
    }
    
    c_lower = company_name.lower()
    aliases = COMPANY_ALIASES.get(c_lower, [company_name])
    
    conditions = []
    for alias in aliases:
        term = f"%{alias}%"
        conditions.append(Article.company.ilike(term))
        conditions.append(Article.title.ilike(term))
        conditions.append(Article.content.ilike(term))
        
    filter_cond = or_(*conditions)

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
        company_name=company_name,
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
    
    # Try to find matching companies
    companies = (
        db.query(Article.company, func.count(Article.id).label("mentions"))
        .filter(Article.company.ilike(search_term))
        .filter(Article.company != None)
        .filter(Article.company != "")
        .group_by(Article.company)
        .order_by(desc("mentions"))
        .limit(5)
        .all()
    )
    
    suggestions = [c[0] for c in companies if c[0]]
    
    # If not enough companies, fallback to title matching for partial entities
    if len(suggestions) < 5:
        titles = (
            db.query(Article.title)
            .filter(Article.title.ilike(f"%{query}%"))
            .limit(20)
            .all()
        )
        import re
        for (title,) in titles:
            if title:
                words = re.findall(r'\b[A-Z][a-z]+\b', title)
                for w in words:
                    if w.lower().startswith(query.lower()) and w not in suggestions and len(w) > 2:
                        suggestions.append(w)
                    if len(suggestions) >= 5:
                        break
            if len(suggestions) >= 5:
                break
                
    return suggestions
