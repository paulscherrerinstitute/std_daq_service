FROM paulscherrerinstitute/std-daq-service-base:1.0.5

COPY . /std_daq_service/
WORKDIR /std_daq_service
RUN echo "$(pwd)" > /opt/conda/lib/python3.9/site-packages/conda.pth

