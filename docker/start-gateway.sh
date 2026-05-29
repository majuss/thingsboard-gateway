#!/bin/sh
# Hardened thingsboard-gateway start script (BACnet-only).
set -eu

CONF_FOLDER="/thingsboard_gateway/config"
FIRSTLAUNCH="${CONF_FOLDER}/.firstlaunch"

if [ ! -f "$FIRSTLAUNCH" ]; then
    cp -r /default-config/config/. /thingsboard_gateway/config/
    cp -r /default-config/extensions/. /thingsboard_gateway/extensions/
    touch "$FIRSTLAUNCH"
    echo "# Delete this file to recreate default config files (will overwrite)." > "$FIRSTLAUNCH"
fi

exec python /thingsboard_gateway/tb_gateway.py
