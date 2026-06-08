# AI Financial Intelligence Platform - Backend Architecture and Functionality

This document provides a comprehensive overview of the backend capabilities, processing pipelines, and core functionalities built into the AI Financial Intelligence Platform. It specifically excludes all frontend and web-facing components.

## Project Goal
The platform is designed to be a scalable, real-time financial intelligence system that continuously collects market information from multiple external sources, processes it through distributed pipelines, performs NLP-based sentiment analysis, generates sentiment forecasts, and exposes this data via a robust API for intelligence dashboards.

## Core System Flow
The architecture follows a production-grade distributed pipeline:
`External Data Sources` -> `Data Ingestion Layer` -> `Redis Queue` -> `Background Workers` -> `NLP Sentiment & Forecasting` -> `PostgreSQL Database` -> `FastAPI Backend`

---

## 1. Data Ingestion Service (`apps/ingest`)
This module is responsible for retrieving and standardizing raw financial news.
- **RSS Fetchers**: Connects to multiple external financial news providers, currently including Reuters, Yahoo Finance, MarketWatch, CNBC, and Seeking Alpha.
- **Transformer Service**: Processes raw fetched data by stripping HTML, normalizing dates, and mapping different source structures to a unified `Article` schema.
- **Pipeline Orchestrator**: Manages the ingestion flow (Fetch -> Transform -> Push to Queue). Instead of blocking via HTTP calls, it seamlessly pushes the transformed articles to a Redis queue for asynchronous background processing.

## 2. Queue & Messaging System (`packages/queue`)
To decouple ingestion from heavy NLP workloads, the system utilizes **Redis** as a distributed message broker.
- **Queue Segregation**: Different queues manage different workloads:
  - Article storage queue
  - Sentiment processing queue (`sentiment_process_queue`)
  - Forecast generation queue (`forecast_queue`)
- **Resilience**: The queue system implements retry logic (e.g., Retry max=3, interval=[10, 30, 60] seconds) to gracefully handle failed jobs.

## 3. Distributed Background Workers (`apps/worker`)
Using Python's `rq` (Redis Queue), multiple background workers handle separate processing phases. This ensures that heavy ML models do not block fast data ingestion.

### A. Article Worker
- **Function**: Quickly picks up raw articles from the Redis queue and performs fast database inserts (~5ms each) into PostgreSQL.
- **Chaining**: Upon successful storage, it automatically pushes a new job to the Sentiment queue containing the article ID for downstream processing.

### B. NLP Sentiment Worker (`run_sentiment.py`)
- **Function**: Performs advanced Natural Language Processing (NLP) on the ingested text.
- **Model Used**: Integrates HuggingFace's `ProsusAI/finbert` model (specifically fine-tuned for financial sentiment analysis).
- **Process**: Runs FinBERT inference on article content, classifying market sentiment as **Positive**, **Negative**, or **Neutral**, and assigns a confidence score.
- **Optimization**: The large ~440MB model is loaded solely into this worker's memory, ensuring that other services remain lightweight and unblocked.

### C. Forecasting Worker (`run_forecast.py`)
- **Function**: Analyzes historical sentiment data and market trends to predict future sentiment movement.
- **Model Used**: Implements forecasting models (like Prophet) which are computationally heavy.
- **Scheduling**: Runs on a separate `forecast_generation` queue to ensure that long-running training or prediction tasks do not halt the real-time sentiment pipeline.

## 4. Core Backend API (`apps/api`)
Built with **FastAPI**, this service provides the primary interface for any client to query the processed market intelligence data. The API is modularized into several routers:

- **Articles API (`/articles`)**: Endpoints to list and paginate through all ingested and processed financial articles.
- **Sentiment API (`/sentiment`)**: Endpoints to fetch analyzed sentiment trends and classification scores for market data.
- **Forecast API (`/forecast`)**: Endpoints for retrieving AI-generated sentiment predictions and confidence scores for future market movement.
- **Analytics API (`/analytics`)**: 
  - `/stats`: Returns aggregate statistics (e.g., total articles processed, overall market sentiment).
  - `/activity-feed`: Provides a unified real-time feed of recent pipeline activity.
  - `/timeseries`: Serves historical sentiment timeseries data for charting.
  - `/topics`: Identifies and groups the top positive and negative market topics over a given timeframe.
- **Intelligence API (`/intelligence/{company_name}`)**: A specialized endpoint that returns a comprehensive, aggregated intelligence report for a specifically queried company.

## 5. Database Architecture
- **Engine**: PostgreSQL (currently running locally, ready for Dockerization).
- **ORM**: Uses SQLAlchemy to manage the schema and interact with the `market_intelligence` database.
- **Storage**: Maintains tables for Articles, their computed Sentiment Analysis scores, and Forecasting models, all highly structured to quickly serve complex analytical queries.

---

## Future Planned Implementations (Backend)
- **Vector Database (FAISS)**: Implementing vector embeddings for semantic search.
- **AI Explanation Layer (RAG)**: Upgrading from simple pretrained models to an advanced LLM-based Retrieval-Augmented Generation (RAG) architecture. This will allow the system to explain *why* sentiment shifted (e.g., AI Analyst answering "Why did sentiment fall?").
