# Epics buffer
This service connects to Epics channels and stores their values in a Redis database.
In addition it allows for pulse_id to timestamp mapping by saving a pulse_id channel (this is not mandatory).

The retrieval and writing of Epics channels is implemented in the [Epics writer](../epics_writer/README.md) service.

## Requirements 
To run this service you will need:
- A running Redis instance.
- IOC sources to connect to.
- Docker

## Configuration
The service needs the following parameters:
- Config file (specifies the PV list and the pulse_id)
- Environment variable REDIS_HOST (default: 127.0.0.1)
- Environment variable SERVICE_NAME
- Environment variable EPICS_CA_ADDR_LIST (if needed)

This service is static in the sense that once started it cannot be reconfigured. You will need to restart it with 
new parameters.

### Configuration file
The configuration file is a JSON file that contains the **pulse\_id\_pv** and **pv\_list** keys in a dictionary.
An example of the configuration file can be found in **tests/redis\_configs/debug.epics\_buffer.json**

```json
{
  "pulse_id_pv": "ioc:pulse_id",
  "pv_list": [
    "ioc:pv_1",
    "ioc:pv_2",
    "ioc:pv_3"
  ]
}
```

## Running the service
Start the service by running the docker container:

```bash
docker run --net=host --rm  \
    --name debug.epics_buffer \
    -e SERVICE_NAME=debug.epics_buffer \
    -e REDIS_HOST=127.0.0.1 \
    -e EPICS_CA_ADDR_LIST=sf-daq-cagw.psi.ch:5062 \
    -v $(pwd)/tests/redis_configs/debug.epics_buffer.json:/std_daq_service/config.json \
    paulscherrerinstitute/std-daq-service \
    epics_buffer
```

Please adjust the **SERVICE\_NAME** (also docker --name flag; the docker container name should match the SERVICE_NAME) 
to the correct name and config mount (-v flag) to point to the correct file.

## Monitoring

You can monitor the performance metrics of the service by running (in the host machine, while the buffer container 
is active):
```bash
docker exec -it debug.epics_buffer tail -f /var/log/std-daq/perf.log
```

The output is in InfluxDB line protocol. This command can also be used to periodically read the metrics and 
send them to InfluxDB.
