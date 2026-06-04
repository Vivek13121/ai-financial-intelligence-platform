# Architecture Plan (Initialization)

## Goals
- Keep services modular and independently deployable.
- Separate ingestion, processing, and delivery concerns.
- Support real-time and batch workloads without code coupling.
- Make it easy to scale specific bottlenecks (ingestion, NLP, websockets, etc.).

## High-Level System Layout
- Ingestion service collects raw market data and normalizes it.
- API service exposes application-facing endpoints and writes to the database.
- Worker service consumes queue tasks for processing, NLP, and forecasting.
- Realtime service pushes updates to clients via WebSocket channels.
- Shared packages define schemas and pipeline contracts used across services.

## Folder Structure (Why Each Exists)

### apps/
- Purpose: deployable services with clear boundaries and runtime ownership.

#### apps/api/
- Why: core FastAPI service for REST endpoints, auth, and coordination.
- Owns: API routes, request validation, database orchestration.

#### apps/ingest/
- Why: isolates external data collection from internal processing.
- Owns: connectors for news/RSS/vendors, normalization, source health.

#### apps/worker/
- Why: queue-driven background processing for heavy tasks.
- Owns: NLP pipelines, forecasting jobs, retry logic, failure handling.

#### apps/realtime/
- Why: dedicated WebSocket gateway to avoid coupling with API latency.
- Owns: socket connections, pub/sub bridge, live updates.

### packages/
- Purpose: shared libraries that keep data contracts consistent.

#### packages/shared/
- Why: shared utilities, logging, configuration helpers.
- Owns: cross-service helpers that are not domain-specific.

#### packages/schemas/
- Why: single source of truth for event and API payloads.
- Owns: Pydantic models or JSON schemas shared by services.

#### packages/pipeline/
- Why: pipeline primitives and task contracts for workers.
- Owns: task definitions, queue payload shapes, processing stages.

### infra/
- Purpose: production infrastructure configuration and deployment assets.

#### infra/docker/
- Why: container build definitions and service-level images.
- Owns: Dockerfiles, build contexts, service image configs.
- Status: **deferred** — Docker setup blocked by local storage/WSL constraints.
  Files retained for future use. No Docker dependency assumed for current phases.

#### infra/db/
- Why: database setup and migrations entry points.
- Owns: migration config, init scripts, seed harness (no seed data yet).

### configs/
- Why: environment-specific configuration templates.
- Owns: base config files, env templates, log/metrics config.

### scripts/
- Why: operational utilities for local dev and CI.
- Owns: lint/test runners, migration commands, bootstrapping scripts.

### tests/
- Why: project-level tests organized by service and integration.
- Owns: contract tests, pipeline tests, basic service health checks.

### docs/architecture/
- Why: keep architecture notes and diagrams separate from code.
- Owns: decisions, diagrams, system specs, runbooks.

## Service Responsibilities (Contract-First)
- Ingest: acquire, normalize, and publish raw events to queue/storage.
- API: expose product-facing features and guard access.
- Worker: process tasks, enrich data, produce insights.
- Realtime: deliver live updates to clients.
- Shared packages: define contracts so services can evolve independently.

## Initial Data Flow (Conceptual)
1. Ingest sources -> normalize -> queue/event store.
2. Worker consumes -> NLP -> forecasting -> insights.
3. API persists results -> exposes endpoints.
4. Realtime service pushes updates to clients.

## Scalability Notes
- Each app is deployable independently for horizontal scaling.
- Queue decouples bursty ingestion from heavy processing.
- Shared schemas reduce integration drift between services.

## Current Infrastructure (Local Development)

| Component  | Setup                          | Notes                                      |
|------------|--------------------------------|--------------------------------------------|
| PostgreSQL | Local Windows installation     | Managed via pgAdmin                        |
| Database   | `market_intelligence`          | Created manually in pgAdmin                |
| DB User    | `postgres`                     | Default superuser                          |
| DB Host    | `localhost:5432`               | No Docker; direct local connection         |
| Docker     | Deferred                       | Blocked by storage/WSL; revisit later      |

DATABASE_URL format:
```
postgresql://postgres:<password>@localhost:5432/market_intelligence
```

When Docker is reintroduced, only the host changes (`localhost` → service name).
No application code changes are required.

## Phase Progress

| Phase | Description               | Status     |
|-------|---------------------------|------------|
| 1     | Backend Foundation        | ✓ Complete |
| 2     | Data Ingestion            | ⬜ Next    |
| 3     | Queue System (Redis)      | ⬜ Planned |
| 4     | Worker Pipelines          | ⬜ Planned |
| 5     | Sentiment Processing      | ⬜ Planned |
| 6     | Forecasting               | ⬜ Planned |
| 7     | AI Explanation Layer      | ⬜ Planned |
| 8     | Frontend Dashboard        | ⬜ Planned |
| 9     | Realtime Updates          | ⬜ Planned |
| 10    | Production Improvements   | ⬜ Planned |

## Next Planned Artifacts
- Service interface specs (API and events).
- Data model outline (tables and relationships only).
- Queue/topic taxonomy.
- Deployment topology sketch.
