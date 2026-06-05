"""
worker/jobs/sentiment_job.py — rq job function for FinBERT sentiment analysis.

Responsibility:
  Receive an article_id (UUID string), fetch the article text from DB,
  run FinBERT inference, and store the result in sentiment_results.

Why FinBERT specifically?
  FinBERT (ProsusAI/finbert) is a BERT model fine-tuned on financial news
  and SEC filings. It understands financial language significantly better
  than general-purpose sentiment models:
    "The company beat earnings expectations" → positive (general models often
    miss the implied positive sentiment here without financial context)
    "Revenue declined amid macro headwinds" → negative (correctly)
    "The Fed held rates steady" → neutral (correctly)

  Output labels: "positive" | "negative" | "neutral"
  Output score:  softmax confidence for the winning label (0.0 – 1.0)

Model loading strategy:
  _SENTIMENT_PIPELINE is a module-level variable initialised to None.
  _get_sentiment_pipeline() loads the model on first call and caches it.
  All subsequent calls return the cached pipeline instantly.

  Why not load in __init__.py?
    rq's SimpleWorker shares the same process, so the model loads once
    when the first job arrives and stays warm for all subsequent jobs.
    Loading at import time would add 3-8s to worker startup even if no
    jobs ever arrive for this queue.

  FinBERT truncation:
    BERT-based models have a hard limit of 512 tokens (~380 words).
    We pass the full article content and let the tokenizer handle truncation
    automatically with truncation=True and max_length=512.
    The headline/lead paragraph carries the strongest sentiment signal.

Retry behaviour:
  If this function raises, rq retries with Retry(max=3, interval=[30,60,120]).
  Transient failures (DB timeout, model OOM) will naturally resolve on retry.
  We always re-raise on real errors — never silently discard sentiment results.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FinBERT pipeline — module-level cache
# ---------------------------------------------------------------------------
# Type annotation only — actual object is a transformers.Pipeline after loading.
_SENTIMENT_PIPELINE: Optional[object] = None

_FINBERT_MODEL = "ProsusAI/finbert"
# Maximum tokens to pass to the model.
_MAX_TOKENS = 512


def _get_sentiment_pipeline():
    """
    Return the cached FinBERT pipeline, loading it on first call.

    This function is NOT thread-safe for the very first call, but since
    rq's SimpleWorker is single-threaded, concurrent first-calls cannot
    happen. If we ever switch to multi-threaded workers, add a threading.Lock.

    Requires transformers 4.x (pinned in requirements.txt).
    transformers 5.x requires torch >= 2.6 which is not installed here.
    """
    global _SENTIMENT_PIPELINE
    if _SENTIMENT_PIPELINE is None:
        logger.info(
            "Loading FinBERT model '%s' (first call — this takes a moment)...",
            _FINBERT_MODEL,
        )
        from transformers import pipeline as hf_pipeline
        _SENTIMENT_PIPELINE = hf_pipeline(
            task="text-classification",
            model=_FINBERT_MODEL,
            # Let the tokenizer handle truncation to max_length.
            truncation=True,
            max_length=_MAX_TOKENS,
            # top_k=1: return only the highest-confidence label.
            top_k=1,
        )
        logger.info("FinBERT model loaded successfully.")
    return _SENTIMENT_PIPELINE


# ---------------------------------------------------------------------------
# rq job function
# ---------------------------------------------------------------------------

def run_sentiment_job(article_id: str) -> None:
    """
    rq job function — run FinBERT on an article and store the result.

    Called by rq after article_job.store_article_job() enqueues it.

    Args:
        article_id: UUID string of the article to process.
                    The article must already be in the `articles` table.

    Steps:
      1. Fetch the article from DB.
      2. Run FinBERT on article.title + ". " + article.content.
      3. Parse the label and score from the pipeline output.
      4. Store the result in sentiment_results via CRUD.

    Raises:
        ValueError  : if article not found (should not happen in normal flow).
        Exception   : any model or DB error — causes rq to retry.
    """
    # Deferred imports so run.py sys.path setup runs first
    from app.database import SessionLocal
    from app import crud
    from app.schemas.sentiment_result import SentimentResultCreate
    from uuid import UUID

    logger.info("Starting sentiment job for article_id=%s", article_id)

    db = SessionLocal()
    try:
        # --- Fetch article ---
        from app.models.article import Article
        article = db.query(Article).filter(Article.id == UUID(article_id)).first()
        if article is None:
            raise ValueError(
                f"sentiment_job: article_id={article_id!r} not found in DB. "
                "This should not happen — article_job must store before enqueuing."
            )

        # --- Build input text ---
        # Combine title + content for richer context.
        # FinBERT handles both parts of a news article equally well.
        # We rely on the tokenizer for truncation.
        text_input = f"{article.title}. {article.content}"

        # --- Run FinBERT ---
        nlp = _get_sentiment_pipeline()
        raw_output = nlp(text_input)

        # transformers returns [[{"label": "positive", "score": 0.97}]]
        # when top_k=1 — unwrap both list levels.
        result_dict = raw_output[0][0] if isinstance(raw_output[0], list) else raw_output[0]
        label: str = result_dict["label"].lower()    # normalise to lowercase
        score: float = float(result_dict["score"])

        logger.info(
            "FinBERT result for article_id=%s: label=%r score=%.4f",
            article_id, label, score,
        )

        # --- Store result ---
        result_in = SentimentResultCreate(
            article_id=UUID(article_id),
            sentiment_label=label,
            score=score,
            model_name=_FINBERT_MODEL,
        )
        sentiment_result = crud.sentiment_result.create_sentiment_result(
            db=db, result_in=result_in
        )
        logger.info(
            "Stored sentiment result id=%s for article_id=%s",
            sentiment_result.id,
            article_id,
        )

    except Exception as exc:
        logger.error("Sentiment job failed for article_id=%s: %s", article_id, exc)
        raise   # let rq retry
    finally:
        db.close()
