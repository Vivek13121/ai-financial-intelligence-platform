# ============================================================
# Dockerfile — API Service
# ============================================================
#
# Why multi-stage build?
#   Stage 1 (builder): installs all Python dependencies into a
#   virtual environment so we get a clean, reproducible layer
#   that is cached by Docker between rebuilds.
#
#   Stage 2 (runtime): copies only the venv and source code —
#   no build tools, no pip, no cache. Smaller final image and
#   a reduced attack surface.
#
# Why python:3.11-slim?
#   The slim variant is ~50MB vs ~350MB for the full image.
#   It includes just enough OS packages to run Python.
#   We avoid -alpine here because psycopg2 needs glibc, not musl.
#
# ============================================================

# ---------- Stage 1: dependency installation ----------
FROM python:3.11-slim AS builder

# Prevents Python from writing .pyc files to disk and
# ensures stdout/stderr are unbuffered (essential for Docker logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Copy only the requirements file first so this layer is cached
# and only re-runs when requirements.txt actually changes.
COPY requirements.txt .

# Install dependencies into an isolated venv inside the build stage.
# Using a venv inside Docker means the final stage can just copy it.
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip --quiet && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: runtime image ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Tell Python to use the venv we built in stage 1
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy the pre-built virtual environment from the builder stage.
COPY --from=builder /opt/venv /opt/venv

# Copy application source code.
# Copying source after venv means source-code changes don't
# invalidate the (expensive) dependency layer.
COPY app/ ./app/

# Expose the port uvicorn will listen on.
# This is documentation; the actual binding is in the CMD.
EXPOSE 8000

# Run the API server.
# --host 0.0.0.0  → listen on all interfaces (required inside Docker).
# --port 8000     → matches EXPOSE above.
# --reload        → auto-reload on code changes (dev only; remove in prod).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
