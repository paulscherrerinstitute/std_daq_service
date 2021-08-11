#!/bin/bash
set -e

docker-compose up -d

for config_file in tests/local_configs/*.json; do
  service_name="$(basename "${config_file}" .json)"

  if [ ! -f "${config_file}" ]; then
    echo "Error: Config file ${config_file} not found"
    continue
  fi

  echo "Setting config from ${config_file} to redis under '${service_name}'."

  redis-cli -x set local_configs.debug.test_pipeline < docker/example_detector.json
done
