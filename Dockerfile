FROM paulscherrerinstitute/std-daq-service-base:1.1.0

COPY . /std_daq_service/
WORKDIR /std_daq_service

RUN python setup.py develop
