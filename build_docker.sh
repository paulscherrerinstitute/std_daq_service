#!/bin/bash

VERSION=1.0.11

set -e

docker build --no-cache=true -t paulscherrerinstitute/std-daq-service .
docker tag paulscherrerinstitute/std-daq-service paulscherrerinstitute/std-daq-service:$VERSION

docker login
docker push paulscherrerinstitute/std-daq-service:$VERSION
docker push paulscherrerinstitute/std-daq-service