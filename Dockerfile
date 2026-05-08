# Multi-stage build keeps the final image small by isolating pip's build
# artifacts in the builder stage.
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Carry the user-site packages from the builder; --user installs land in
# /root/.local which is small and self-contained.
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Application code only. tests/ and dev-only files are excluded via .dockerignore.
COPY app/ ./app/

# Create the data directory at build time so the first CSV export does not
# fail on a fresh container with no writable parent.
RUN mkdir -p /app/data

EXPOSE 8000

# Hosts that inject $PORT (Render, Railway) override the default; otherwise
# fall back to 8000 for local `docker run` use.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
