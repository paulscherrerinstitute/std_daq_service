#!/bin/bash

set -e

cd ../ &&
  docker build -t unittest-std-daq-service:latest . &&
  docker run --rm --net=host \
    --env PIPELINE_NAME=debug.test_pipeline \
    --env SERVICE_NAME=epics_buffer \
   unittest-std-daq-service:latest \
   python -m unittest discover tests/
