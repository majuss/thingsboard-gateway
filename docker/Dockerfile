FROM python:slim-trixie AS builder

ARG TARGETPLATFORM
ARG BUILDPLATFORM

ENV PATH="/root/.cargo/bin:$PATH" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY . /build

RUN set -eux; \
    echo "Running on ${BUILDPLATFORM}, building for ${TARGETPLATFORM}" > /build.log; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        python3-dev \
        libssl-dev \
        libffi-dev \
        zlib1g-dev \
        curl \
        pkg-config; \
    case "${TARGETPLATFORM}" in \
        "linux/amd64") DEFAULT_HOST="x86_64-unknown-linux-gnu" ;; \
        "linux/386") DEFAULT_HOST="i686-unknown-linux-gnu" ;; \
        "linux/arm64") DEFAULT_HOST="aarch64-unknown-linux-gnu" ;; \
        "linux/arm/v7") DEFAULT_HOST="armv7-unknown-linux-gnueabihf" ;; \
        *) DEFAULT_HOST="x86_64-unknown-linux-gnu" ;; \
    esac; \
    curl https://sh.rustup.rs -sSf | sh -s -- -y --default-host="${DEFAULT_HOST}" --profile minimal; \
    python -m pip install --upgrade pip wheel; \
    python -m pip wheel --wheel-dir /wheels -r requirements.txt; \
    python -m pip wheel --wheel-dir /wheels .; \
    rustup self uninstall -y || { \
        echo "rustup uninstall failed, removing manually..."; \
        rm -rf /root/.rustup /root/.cargo; \
    }; \
    apt-get purge -y --auto-remove \
        build-essential \
        gcc \
        python3-dev \
        libssl-dev \
        libffi-dev \
        zlib1g-dev \
        curl \
        pkg-config; \
    rm -rf /var/lib/apt/lists/* /tmp/*

FROM python:slim-trixie AS runtime

ENV PYTHONPATH="." \
    configs="/thingsboard_gateway/config" \
    extensions="/thingsboard_gateway/extensions" \
    logs="/thingsboard_gateway/logs" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY --from=builder /wheels /wheels
COPY ./thingsboard_gateway /thingsboard_gateway
COPY ./requirements.txt /requirements.txt

RUN set -eux; \
    mkdir -p /default-config/config /default-config/extensions; \
    cp -r /thingsboard_gateway/config/* /default-config/config/; \
    cp -r /thingsboard_gateway/extensions/* /default-config/extensions/; \
    python -m pip install --upgrade pip; \
    python -m pip install --no-index --find-links=/wheels -r /requirements.txt; \
    python -m pip install --no-index --find-links=/wheels /wheels/thingsboard_gateway-*.whl; \
    rm -rf /wheels /tmp/*; \
    printf '%s\n' \
      '#!/bin/sh' \
      'set -eu' \
      'CONF_FOLDER="/thingsboard_gateway/config"' \
      'FIRSTLAUNCH="${CONF_FOLDER}/.firstlaunch"' \
      'if [ ! -f "$FIRSTLAUNCH" ]; then' \
      '    cp -r /default-config/config/* /thingsboard_gateway/config/' \
      '    cp -r /default-config/extensions/* /thingsboard_gateway/extensions/' \
      '    touch "$FIRSTLAUNCH"' \
      '    echo "#Remove this file only if you want to recreate default config files! This will overwrite existing files" > "$FIRSTLAUNCH"' \
      'fi' \
      'exec python /thingsboard_gateway/tb_gateway.py' > /start-gateway.sh; \
    chmod +x /start-gateway.sh

VOLUME ["${configs}", "${extensions}", "${logs}"]

CMD ["/bin/sh", "/start-gateway.sh"]
