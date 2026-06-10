from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.intelligence import CompanyIntelligence, AISummaryResponse, AISummaryStatusResponse
from app.crud.intelligence import get_company_intelligence
from app.services.cache_service import get_cache, set_cache
from app.services.ai_service import generate_company_summary
from datetime import datetime

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
)

@router.get("/suggestions", response_model=list[str])
def read_search_suggestions(q: str, db: Session = Depends(get_db)):
    """
    Returns autocomplete suggestions for the search query.
    """
    if not q or len(q) < 2:
        return []
    from app.crud.intelligence import get_search_suggestions
    return get_search_suggestions(db, q)

@router.get("/{company_name}", response_model=CompanyIntelligence)
def read_company_intelligence(company_name: str, db: Session = Depends(get_db)):
    """
    Returns a comprehensive intelligence dashboard for a specific company.
    """
    if not company_name or len(company_name) < 2:
        raise HTTPException(status_code=400, detail="Invalid company name")
        
    return get_company_intelligence(db, company_name)

@router.get("/{company_name}/summary/status", response_model=AISummaryStatusResponse)
def get_ai_summary_status(company_name: str):
    """
    Checks if a generated summary exists in cache.
    """
    cache_key = f"intelligence:summary:{company_name.lower()}"
    cached_summary = get_cache(cache_key)
    if cached_summary:
        return {"is_cached": True, "generated_at": cached_summary.get("generated_at")}
    return {"is_cached": False, "generated_at": None}

@router.get("/{company_name}/summary", response_model=AISummaryResponse)
def get_ai_summary(company_name: str, db: Session = Depends(get_db)):
    """
    Returns an AI generated intelligence summary for the company.
    Cached for 6 hours.
    """
    if not company_name or len(company_name) < 2:
        raise HTTPException(status_code=400, detail="Invalid company name")

    cache_key = f"intelligence:summary:{company_name.lower()}"
    cached_summary = get_cache(cache_key)
    
    if cached_summary:
        return cached_summary

    intel_data = get_company_intelligence(db, company_name)
    
    articles = intel_data.news_feed[:10]
    current_sentiment = intel_data.overview.current_sentiment
    forecast_direction = intel_data.overview.forecast_direction

    try:
        summary = generate_company_summary(company_name, articles, current_sentiment, forecast_direction)
        summary["generated_at"] = datetime.utcnow().isoformat() + "Z"
        set_cache(cache_key, summary, 21600)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate AI summary. Error: {str(e)}")
