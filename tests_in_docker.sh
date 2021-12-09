#!/bin/bash

set -e

docker build -t unittest-std-daq-service:latest .

docker run --rm --net=host \
  --env SERVICE_NAME=debug.test_pipeline.epics_buffer \
  --env REDIS_SKIP=1 \
    unittest-std-daq-service:latest \
    python -m unittest discover tests/
