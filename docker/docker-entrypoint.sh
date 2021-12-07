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
  REDIS_CONFIG_KEY=config."${SERVICE_NAME}"
  REDIS_STATUS_KEY=status."${SERVICE_NAME}"

  redis-cli -h "${REDIS_HOST}" get "${REDIS_CONFIG_KEY}" > config.json

  CONFIG_BYTES="$(stat -c %s config.json)"
  if [ "${CONFIG_BYTES}" -le 1 ]; then
      echo "Key missing in redis(${REDIS_HOST}): ${REDIS_CONFIG_KEY}"
      exit 1;
  fi

  export REDIS_STATUS_KEY
  redis_status.sh &
fi

EXECUTABLE="${@:1}"
exec $EXECUTABLE
