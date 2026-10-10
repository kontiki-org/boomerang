FROM python:3.12-slim

WORKDIR /app

# Avoid writing .pyc and ensure unbuffered logs.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -U pip

COPY pyproject.toml poetry.lock README.md ./
COPY packages/boomerang-contracts ./packages/boomerang-contracts
COPY boomerang ./boomerang

# Install the service package (includes kontiki dependency via pyproject).
RUN pip install --no-cache-dir .

# SERVICE is the image identity. It must match a boomerang-<service> command.
# VERSION is the tag announced to the registry. Both are empty for a local build
# that still starts an explicit boomerang-* command.
ARG SERVICE=
ARG VERSION=
ENV SERVICE=$SERVICE
ENV BOOMERANG_VERSION=$VERSION
COPY docker/entrypoint.sh /usr/local/bin/boomerang-entrypoint
RUN chmod +x /usr/local/bin/boomerang-entrypoint \
    && if [ -n "$SERVICE" ] && [ ! -x "/usr/local/bin/boomerang-$SERVICE" ]; then \
         echo "Unknown service: $SERVICE" >&2; \
         exit 1; \
       fi
ENTRYPOINT ["boomerang-entrypoint"]

