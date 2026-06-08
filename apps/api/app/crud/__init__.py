# apps/api/app/crud/__init__.py
# Expose crud sub-modules so callers can do:
#   from app import crud
#   crud.article.create_article(...)
#   crud.sentiment_result.create_sentiment_result(...)
from app.crud import article          # noqa: F401
from app.crud import sentiment_result  # noqa: F401
from app.crud import forecast_result   # noqa: F401
from app.crud import analytics         # noqa: F401
