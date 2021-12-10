#!/bin/bash

set -e

docker build -t unittest-std-daq-service:latest .

docker run --rm --net=host \
    --entrypoint "" \
    unittest-std-daq-service:latest \
    python -m unittest discover tests/
