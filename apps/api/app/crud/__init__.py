# apps/api/app/crud/__init__.py
# Expose crud sub-modules so callers can do:
#   from app import crud
#   crud.article.create_article(...)
from app.crud import article  # noqa: F401
