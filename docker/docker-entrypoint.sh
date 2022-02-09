#!/bin/bash
set -e

REDIS_SKIP="${REDIS_SKIP:-false}"

# Download config from Redis to config.json and start status reporting.
if [ "${REDIS_SKIP}" = false ]; then

  if [[ -z "${SERVICE_NAME}" ]]; then
    echo "Environment variable SERVICE_NAME not defined."
    exit 1;
  fi

  REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
  REDIS_PORT="${REDIS_PORT:-6379}"
  REDIS_STATUS_KEY=status."${SERVICE_NAME}"

  export REDIS_STATUS_KEY
  export SERVICE_NAME
  export REDIS_HOST
  export REDIS_PORT
  redis_status.sh &
fi

if [ ! -f config.json ]; then
  echo "[INFO] No config.json file mapped to container. Creating default."
  echo "{}" > config.json
fi

EXECUTABLE="${@:1}"
exec $EXECUTABLE
