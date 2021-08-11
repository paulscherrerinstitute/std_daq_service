FROM paulscherrerinstitute/std-daq-service-base:1.0.2

COPY . /std_daq_service/

RUN cp /std_daq_service/docker/example_detector.json /std_daq_service && \
    cd /std_daq_service

WORKDIR /std_daq_service
