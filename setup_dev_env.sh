#!/bin/bash
set -e

docker-compose up -d

for config_file in tests/redis_configs/*.json; do
  service_name="$(basename "${config_file}" .json)"

  if [ ! -f "${config_file}" ]; then
    echo "Error: no config files were found in ${config_file}"
    continue
  fi

  REDIS_KEY=config."${service_name}"

  echo "Setting config ${config_file} to Redis."

  redis-cli -x set "${REDIS_KEY}" < "${config_file}"
done