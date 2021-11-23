FROM paulscherrerinstitute/std-daq-service-base:1.0.5

COPY . /std_daq_service/

RUN cp /std_daq_service/docker/example_detector.json /std_daq_service && \
    cd /std_daq_service && \
    echo "$(pwd)" > /opt/conda/lib/python3.9/site-packages/conda.pth

WORKDIR /std_daq_service
