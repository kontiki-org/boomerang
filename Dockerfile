FROM python:3.12-slim

WORKDIR /app

# Avoid writing .pyc and ensure unbuffered logs.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -U pip

COPY pyproject.toml poetry.lock README.md ./
COPY boomerang ./boomerang

# Install the service package (includes kontiki dependency via pyproject).
RUN pip install --no-cache-dir .

