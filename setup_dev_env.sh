#!/bin/bash
set -e

docker-compose up -d

for config_file in tests/local_configs/*.json; do
  service_name="$(basename "${config_file}" .json)"

  if [ ! -f "${config_file}" ]; then
    echo "Error: Config file ${config_file} not found"
    continue
  fi

  REDIS_KEY=config."${service_name}"

  echo "Setting config from ${config_file} to Redis under '${REDIS_KEY}'."

  redis-cli -x set "${REDIS_KEY}" < "${config_file}"
done
