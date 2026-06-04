"""
fetchers/__init__.py — marks this directory as a Python package.

Why a fetchers/ sub-package?
  The fetcher layer is purely responsible for COLLECTING raw data from
  external sources. As we add more source types (WebSocket streams,
  paid news APIs, social feeds), each gets its own fetcher module:

    fetchers/rss.py       ← RSS/Atom feeds (current)
    fetchers/newsapi.py   ← NewsAPI.org (future)
    fetchers/twitter.py   ← Twitter/X stream (future)

  Keeping fetchers isolated means the service layer never cares WHERE
  the data came from — it only cares about the raw content it receives.
"""
