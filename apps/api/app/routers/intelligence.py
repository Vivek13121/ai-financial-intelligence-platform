from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.intelligence import CompanyIntelligence
from app.crud.intelligence import get_company_intelligence

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
