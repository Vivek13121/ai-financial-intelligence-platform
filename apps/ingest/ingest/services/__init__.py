"""
services/__init__.py — marks this directory as a Python package.

Why a services/ sub-package?
  The service layer sits between fetchers and the API client.
  Its single responsibility: transform raw external data into the
  clean internal format the backend API expects.

  Future services might be added here:
    services/transformer.py   ← RSS → ArticleCreate (current)
    services/deduplicator.py  ← skip articles already stored (future)
    services/enricher.py      ← extract company names via NER (future Phase 5)
"""
