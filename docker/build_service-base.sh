#!/bin/bash

VERSION=1.1.2

set -e

docker build --no-cache=true -f service-base.Dockerfile -t paulscherrerinstitute/std-daq-service-base .
docker tag paulscherrerinstitute/std-daq-service-base paulscherrerinstitute/std-daq-service-base:$VERSION

docker login
docker push paulscherrerinstitute/std-daq-service-base:$VERSION
docker push paulscherrerinstitute/std-daq-service-base