#!/bin/bash

cd ../../ &&
  docker build -t debug-std-daq-service . &&
  docker run --name debug-std-daq-service --net=host \
    --env PIPELINE_NAME=debug.test_pipeline \
    --env SERVICE_NAME=epics_buffer \
   debug-std-daq-service
