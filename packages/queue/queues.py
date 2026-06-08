"""
packages/queue/queues.py — Queue name registry and queue factory.

Why centralise queue names here?
  If the ingest service pushes to "article_ingest" but the worker listens
  on "articles", nothing works — and the bug is completely silent (jobs
  just pile up unprocessed). A single source of truth for queue names
  eliminates this entire class of bugs.

Queue naming convention:
  <domain>_<action>   e.g. article_ingest, sentiment_process, forecast_run

  This makes it obvious which queue belongs to which pipeline stage.
  Current queues:
    ARTICLE_INGEST_QUEUE_NAME    = "article_ingest"     ← Phase 3 (active)
    SENTIMENT_PROCESS_QUEUE_NAME = "sentiment_process"  ← Phase 4 (active)
  Future queues:
    FORECAST_RUN_QUEUE_NAME      = "forecast_run"       ← Phase 6

rq.Queue:
  Queue(name, connection=...) creates a logical queue backed by a Redis
  list. The queue name maps directly to a Redis key: "rq:queue:<name>".
  Multiple producers can push to the same queue; multiple workers can
  consume from it — both are safe.
"""

import rq

from packages.queue.connection import get_redis_connection

# ---------------------------------------------------------------------------
# Queue name constants
# ---------------------------------------------------------------------------

ARTICLE_INGEST_QUEUE_NAME    = "article_ingest"
SENTIMENT_PROCESS_QUEUE_NAME = "sentiment_process"
FORECAST_GENERATION_QUEUE_NAME = "forecast_generation"


# ---------------------------------------------------------------------------
# Queue factories
# ---------------------------------------------------------------------------

def get_article_queue() -> rq.Queue:
    """
    Return an rq.Queue connected to the article_ingest queue.

    Called by the ingest service to enqueue jobs.
    Called by the worker to declare which queue it listens on.

    A new Queue object is cheap to create — rq doesn't make network calls
    until you actually enqueue or dequeue a job. Safe to call frequently.
    """
    conn = get_redis_connection()
    return rq.Queue(
        name=ARTICLE_INGEST_QUEUE_NAME,
        connection=conn,
        # default_timeout: how long a single job can run before rq kills it.
        # 60s is generous for a simple DB insert; increase for heavier jobs.
        default_timeout=60,
    )


def get_sentiment_queue() -> rq.Queue:
    """
    Return an rq.Queue connected to the sentiment_process queue.

    Called by article_job (producer) after storing an article.
    Called by the sentiment worker to declare which queue it listens on.

    default_timeout is 300s because FinBERT inference on CPU can be slow
    on first load (model initialisation) and under load. After the model
    is warm the actual inference time is typically 0.1–1s per article.
    """
    conn = get_redis_connection()
    return rq.Queue(
        name=SENTIMENT_PROCESS_QUEUE_NAME,
        connection=conn,
        default_timeout=300,
    )


def get_forecast_queue() -> rq.Queue:
    """
    Return an rq.Queue connected to the forecast_generation queue.

    Called when we want to trigger a new forecast generation.
    default_timeout is 300s because Prophet can take a few seconds to train
    depending on the size of the dataset.
    """
    conn = get_redis_connection()
    return rq.Queue(
        name=FORECAST_GENERATION_QUEUE_NAME,
        connection=conn,
        default_timeout=300,
    )

