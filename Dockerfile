# syntax=docker/dockerfile:1

FROM node:24-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim AS runtime
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DRIVEGUARD_STATIC_DIR=/opt/driveguard/static \
    PORT=10000
WORKDIR /opt/driveguard
COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app
RUN python -m pip install . \
    && useradd --system --uid 10001 --create-home driveguard
COPY --from=frontend-build /build/frontend/dist ./static
USER 10001
EXPOSE 10000
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
