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

  if [ -f config.json ]; then
    echo "Local config.json file detected. Skipping Redis download."
  else
    redis-cli -h "${REDIS_HOST}" get "${REDIS_CONFIG_KEY}" > config.json

    CONFIG_BYTES="$(stat -c %s config.json)"
    if [ "${CONFIG_BYTES}" -le 1 ]; then
      echo "Key missing in redis(${REDIS_HOST}): ${REDIS_CONFIG_KEY}"
      echo "Initializing empty json file."
      echo "{}" > config.json
    fi
  fi

  export REDIS_STATUS_KEY
  redis_status.sh &
fi

if [ -f config.json ]; then
  CONFIG_BYTES="$(stat -c %s config.json)"
  if [ "${CONFIG_BYTES}" -le 1 ]; then
    echo "Provided empty config.json file. Do not provide the file if not needed by the service."
    exit 1;
  fi
else
  echo "No config.json file. Initializing empty json file."
  echo "{}" > config.json
fi

EXECUTABLE="${@:1}"
exec $EXECUTABLE
