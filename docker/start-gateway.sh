#!/bin/sh
set -eu

CONF_FOLDER="${TB_GW_CONFIG_DIR:-/thingsboard_gateway/config}"
FIRSTLAUNCH="${CONF_FOLDER}/.firstlaunch"

mkdir -p "${CONF_FOLDER}" /thingsboard_gateway/extensions /thingsboard_gateway/logs

if [ ! -f "${FIRSTLAUNCH}" ]; then
    cp -a /default-config/config/. "${CONF_FOLDER}/"
    cp -a /default-config/extensions/. /thingsboard_gateway/extensions/
    printf '%s\n' "# Remove this file only if you want to recreate default config files. This will overwrite existing files." > "${FIRSTLAUNCH}"
fi

exec python /thingsboard_gateway/tb_gateway.py
