"""
worker/__init__.py — marks this directory as a Python package.

Why a worker/ package?
  - Allows `worker.jobs.article_job.store_article_job` to be imported
    by rq when it deserializes jobs from the queue.
  - rq resolves job functions by their full dotted import path, so the
    directory must be a proper Python package with an __init__.py.
  - This is the function path we pass when enqueueing:
      "worker.jobs.article_job.store_article_job"
"""
