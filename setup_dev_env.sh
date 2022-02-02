#!/bin/bash
set -e

docker-compose up -d
sleep 1

for config_file in tests/configs/*.json; do
  service_name="$(basename "${config_file}" .json)"

  if [ ! -f "${config_file}" ]; then
    echo "Error: no config files were found in ${config_file}"
    continue
  fi

  REDIS_KEY=config."${service_name}"
  REDIS_STATUS_KEY=status."${service_name}"

  echo "Setting config ${config_file} to Redis."

  redis-cli -x --raw set "${REDIS_KEY}" < "${config_file}"
  redis-cli -x --raw hset "${REDIS_STATUS_KEY}" config < "${config_file}"
  redis-cli --raw hset "${REDIS_STATUS_KEY}" start_timestamp "$(date +%s)"
  redis-cli --raw hset "${REDIS_STATUS_KEY}" service_name "${service_name}"
done
