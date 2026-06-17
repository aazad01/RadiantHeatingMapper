# Containerized radiant heating layout service.
#
# Build:  docker build -t radiant-heat .
# Serve:  docker run --rm -p 8000:8000 radiant-heat
#         -> open http://localhost:8000  (UI) or call /api/layout (services)
# CLI:    docker run --rm radiant-heat compute --length 10 --width 10 --spacing 1
#         docker run --rm radiant-heat svg --length 10 --width 10 -o - > layout.svg
#
# Runs identically on Windows, macOS and Linux via Docker Desktop, which avoids
# the platform-specific native-binary problem of a PyInstaller build.
FROM python:3.12-slim AS base

# Don't write .pyc files; flush stdout/stderr immediately for container logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install dependencies/package first so layers cache well.
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Liveness check against the API's /health endpoint (no curl in slim image).
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'), timeout=3).status==200 else 1)"

# `radiant-heat` is the unified CLI. Default to serving the HTTP API; override
# the command (e.g. `compute ...`) to use the one-shot subcommands instead.
ENTRYPOINT ["radiant-heat"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
