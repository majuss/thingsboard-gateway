# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-alpine AS builder

WORKDIR /build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache \
      build-base \
      linux-headers \
      libffi-dev \
      openssl-dev \
      pkgconf \
      cargo \
      rust

COPY requirements.txt /build/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    python -m pip wheel --wheel-dir=/wheels -r /build/requirements.txt

FROM python:${PYTHON_VERSION}-alpine AS runtime

WORKDIR /thingsboard_gateway
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/ \
    configs=/thingsboard_gateway/config \
    extensions=/thingsboard_gateway/extensions \
    logs=/thingsboard_gateway/logs

RUN apk add --no-cache ca-certificates libstdc++ && \
    update-ca-certificates && \
    addgroup -S tb-gateway && \
    adduser -S -D -h /home/tb-gateway -s /sbin/nologin -G tb-gateway tb-gateway && \
    mkdir -p /default-config/config /default-config/extensions /thingsboard_gateway/config /thingsboard_gateway/extensions /thingsboard_gateway/logs

COPY requirements.txt /tmp/requirements.txt
COPY --from=builder /wheels /wheels

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --no-compile --no-index --find-links=/wheels -r /tmp/requirements.txt && \
    rm -rf /wheels /tmp/requirements.txt

COPY --chown=tb-gateway:tb-gateway thingsboard_gateway /thingsboard_gateway
COPY --chown=tb-gateway:tb-gateway docker/start-gateway.sh /usr/local/bin/start-gateway.sh

RUN cp -a /thingsboard_gateway/config/. /default-config/config/ && \
    cp -a /thingsboard_gateway/extensions/. /default-config/extensions/ && \
    chmod +x /usr/local/bin/start-gateway.sh && \
    chown -R tb-gateway:tb-gateway /default-config

VOLUME ["/thingsboard_gateway/config", "/thingsboard_gateway/extensions", "/thingsboard_gateway/logs"]

USER tb-gateway
CMD ["/usr/local/bin/start-gateway.sh"]
