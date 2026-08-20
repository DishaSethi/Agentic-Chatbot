# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev\
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt


ARG UID=10001
RUN adduser \
  --disabled-password \
  --gecos ""\
  --home "/nonexistent"\
  --shell "/sbin/nologin"\
  --no-create-home \
  --uid "${UID}" \
  appuser

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

CMD ["uvicorn","server:app", "--host","0.0.0.0", "--port","8000","--reload"]

EXPOSE 8000