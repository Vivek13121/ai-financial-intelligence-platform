# apps/api/app/models/__init__.py
# Importing models here ensures SQLAlchemy registers them against Base
# before Base.metadata.create_all() is called in main.py.
# If models are never imported, their tables will not be created.

from app.models.article import Article                  # noqa: F401
from app.models.sentiment_result import SentimentResult  # noqa: F401
from app.models.forecast_result import ForecastResult   # noqa: F401
