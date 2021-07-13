#!/bin/bash

VERSION=1.0.0

docker build --no-cache=true -f service.Dockerfile -t paulscherrerinstitute/std-daq-service .
docker tag paulscherrerinstitute/std-daq-service-base paulscherrerinstitute/std-daq-service:$VERSION

docker login
docker push paulscherrerinstitute/std-daq-service:$VERSION
docker push paulscherrerinstitute/std-daq-service