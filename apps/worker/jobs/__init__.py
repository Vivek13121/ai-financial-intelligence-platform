"""
worker/jobs/__init__.py — marks this directory as a Python package.

Why jobs/ sub-package?
  As we add more pipeline stages, each gets its own job module:
    jobs/article_job.py       ← store raw articles (Phase 3, current)
    jobs/sentiment_job.py     ← run sentiment analysis (Phase 5)
    jobs/forecast_job.py      ← run forecasting model (Phase 6)

  Each module contains exactly one public job function that rq calls.
  This keeps job functions small, focused, and independently testable.
"""
