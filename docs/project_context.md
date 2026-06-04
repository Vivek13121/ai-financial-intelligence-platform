You are helping me build a large-scale production-style AI Financial Intelligence Platform.

Project Goal:

Build an AI-powered real-time financial intelligence platform that continuously collects market information from multiple sources, processes it through scalable pipelines, performs sentiment analysis and forecasting, and generates explainable market insights through an interactive dashboard.

This project should prioritize:

- Scalability
- Production architecture
- Modular design
- Real-time systems
- Distributed processing
- Clean folder structure
- Industry-standard practices
- Maintainability
- Learning-focused explanations while building

====================================================

HIGH LEVEL VISION

Users can:

- Search/select companies, stocks, or market sectors
- View live sentiment trends
- View real-time news streams
- Analyze historical sentiment movement
- View sentiment forecasts
- Ask AI-powered questions about market changes
- Receive explainable insights rather than raw sentiment scores
- Track watchlists
- Monitor live market intelligence dashboards

====================================================

CORE SYSTEM FLOW

External Data Sources

↓

Data Ingestion Layer

↓

Database Storage

↓

Queue System

↓

Background Workers

↓

NLP Processing Pipeline

↓

Sentiment + Forecasting

↓

AI Explanation Layer

↓

Frontend Dashboard

====================================================

TECH STACK

Frontend:

- React
- Vite
- TypeScript
- Tailwind CSS
- Chart libraries
- Socket.io client

Backend:

- FastAPI (Python)

Database:

- PostgreSQL (local installation — no Docker)

Queue System:

- Redis

Background Processing:

- Python workers
- Queue-based architecture

Realtime Communication:

- WebSockets
- Socket.io

AI / NLP Layer:

Initially:

- Simple pretrained sentiment models
- Basic NLP pipelines
- Lightweight inference

Later upgrade to:

- Advanced LLM-based analysis
- Better sentiment pipelines
- RAG architecture
- Agentic workflows
- More accurate forecasting models

Vector Database:

Later phase:

- FAISS initially
- Can upgrade later

Deployment:

- Docker containerization is planned for a later phase.
- Currently: all services run locally (no Docker).

====================================================

INFRASTRUCTURE (CURRENT)

PostgreSQL:

- Installed locally via native Windows installer
- Managed via pgAdmin (local)
- Database name: market_intelligence
- User: postgres
- Host: localhost
- Port: 5432

DATABASE_URL format:

  postgresql://postgres:<password>@localhost:5432/market_intelligence

Why local (not Docker) right now:

- Docker setup was blocked due to local storage constraints and WSL requirements.
- Switching to local PostgreSQL keeps development unblocked.
- Architecture remains unchanged — Docker can be reintroduced later with no code changes
  (only the DATABASE_URL host would change from localhost to the container service name).

====================================================

PHASE PROGRESS

Phase 1 — Backend Foundation: ✓ COMPLETE

  ✓ FastAPI backend running
  ✓ PostgreSQL connection working (local, market_intelligence database)
  ✓ Health endpoint working       GET  /health
  ✓ POST article API working      POST /api/v1/articles
  ✓ GET articles API working      GET  /api/v1/articles
  ✓ Swagger docs working          GET  /docs

Phase 2 — Data Ingestion: ✓ COMPLETE

  ✓ apps/ingest/ ingestion service created
  ✓ RSS fetcher layer (Reuters, Yahoo Finance, MarketWatch, CNBC, Seeking Alpha)
  ✓ Transformer service (HTML stripping, date normalisation, field mapping)
  ✓ Pipeline orchestrator (fetch → transform → POST to API)
  ✓ Manual run entry point: python run.py (from apps/ingest/)
  ✓ article_url field added to Article model + schema + DB (ALTER TABLE)
  ✓ Verified: 91 fetched → 91 transformed → 91 stored → 0 failed
  ✓ GET /api/v1/articles returns real financial news from live RSS feeds

Phase 3 — Queue System (Redis): ⬜ PLANNED
Phase 4 — Worker Pipelines: ⬜ PLANNED
Phase 5 — Sentiment Processing: ⬜ PLANNED
Phase 6 — Forecasting: ⬜ PLANNED
Phase 7 — AI Explanation Layer: ⬜ PLANNED
Phase 8 — Frontend Dashboard: ⬜ PLANNED
Phase 9 — Realtime Updates: ⬜ PLANNED
Phase 10 — Production Improvements: ⬜ PLANNED

====================================================

INITIAL DEVELOPMENT PHILOSOPHY

Do NOT start with frontend.

Development order:

1. Architecture
2. Backend APIs
3. Database setup
4. Data ingestion
5. Queue system
6. Worker pipelines
7. Sentiment processing
8. Forecasting
9. AI explanation layer
10. Frontend dashboard
11. Realtime updates
12. Production improvements

Frontend should come AFTER backend systems exist.

====================================================

FEATURES (FULL VERSION)

DATA INGESTION:

- News APIs
- RSS feeds
- Financial articles
- Company announcements
- Social signals (later)

PIPELINE:

- Queue-based processing
- Retry logic
- Background workers
- Failure handling
- Monitoring

NLP:

- Sentiment Analysis
- Entity Extraction
- Topic Classification
- Article Categorization

FORECASTING:

- Historical sentiment tracking
- Trend analysis
- Forecast generation
- Confidence scores
- Anomaly detection

AI LAYER:

- Retrieval Augmented Generation
- Explainable insights
- AI analyst chatbot
- Ask questions about sentiment movement

FRONTEND:

Dashboard should contain:

1. Overview Metrics

- total articles
- market sentiment
- positive/negative trends
- processing statistics

2. Live Feed

- incoming articles
- processing status
- latest insights

3. Sentiment Visualization

- trend graphs
- timelines
- company comparisons

4. Forecast Panel

- predicted movement
- confidence scores
- anomalies

5. AI Analyst Chat

Users ask:

"Why did sentiment fall?"

AI responds using retrieved data.

6. Watchlists

Users save companies.

7. Realtime Updates

Dashboard updates automatically.

====================================================

CODING RULES

- Prefer modular architecture
- Explain why decisions are made
- Avoid unnecessary abstractions early
- Keep code production-like
- Focus on learning while building
- Never generate entire massive codebases at once
- Build incrementally

====================================================

Whenever suggesting code:

Explain:

- why this component exists
- how it fits architecture
- alternatives if relevant
- best practices

We are building this step by step like a real production system.