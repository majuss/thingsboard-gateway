# syntax=docker/dockerfile:1.7
# Hardened thingsboard-gateway image: BACnet-only, no RemoteShell, no RemoteConfig, no inbound RPCs.

# --- Stage 1: builder -------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

ARG TARGETPLATFORM
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc python3-dev libssl-dev libffi-dev zlib1g-dev pkg-config curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Rust toolchain (needed for cryptography / orjson native builds on non-amd64).
RUN case "${TARGETPLATFORM:-linux/amd64}" in \
        "linux/amd64") DEFAULT_HOST="x86_64-unknown-linux-gnu";; \
        "linux/arm64") DEFAULT_HOST="aarch64-unknown-linux-gnu";; \
        "linux/arm/v7") DEFAULT_HOST="armv7-unknown-linux-gnueabihf";; \
        *) DEFAULT_HOST="x86_64-unknown-linux-gnu";; \
    esac \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --default-host="$DEFAULT_HOST" --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

COPY requirements.txt /build/requirements.txt
RUN pip install --upgrade pip setuptools wheel \
    && pip wheel --wheel-dir /wheels -r requirements.txt

# --- Stage 2: runtime -------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

ARG APP_UID=10001
ARG APP_GID=10001
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="thingsboard-gateway-hardened" \
      org.opencontainers.image.description="Hardened ThingsBoard Gateway (BACnet-only, no RPC/RemoteShell/RemoteConfig)" \
      org.opencontainers.image.source="https://github.com/thingsboard/thingsboard-gateway" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    TB_GW_HARDENED=1 \
    configs="/thingsboard_gateway/config" \
    extensions="/thingsboard_gateway/extensions" \
    logs="/thingsboard_gateway/logs"

RUN apt-get update && apt-get install -y --no-install-recommends \
        tini ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid "${APP_GID}" tbgw \
    && useradd  --system --uid "${APP_UID}" --gid tbgw --home-dir /thingsboard_gateway --shell /usr/sbin/nologin tbgw

WORKDIR /thingsboard_gateway

COPY --from=builder /wheels /wheels
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-index --find-links=/wheels -r /tmp/requirements.txt \
    && rm -rf /wheels /tmp/requirements.txt \
    && pip uninstall -y pip setuptools wheel || true

COPY ./thingsboard_gateway /thingsboard_gateway
COPY ./docker/start-gateway.sh /start-gateway.sh

RUN mkdir -p /default-config/config /default-config/extensions \
              /thingsboard_gateway/logs /thingsboard_gateway/config /thingsboard_gateway/extensions \
    && cp -r /thingsboard_gateway/config/. /default-config/config/ \
    && cp -r /thingsboard_gateway/extensions/. /default-config/extensions/ \
    && chmod +x /start-gateway.sh \
    && chown -R tbgw:tbgw /thingsboard_gateway /default-config

USER tbgw

VOLUME ["/thingsboard_gateway/config", "/thingsboard_gateway/extensions", "/thingsboard_gateway/logs"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import socket,os; socket.create_connection((os.environ.get('TB_GW_HOST','127.0.0.1'), int(os.environ.get('TB_GW_PORT','1883'))), 5)" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/sh", "/start-gateway.sh"]
