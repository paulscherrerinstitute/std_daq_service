# Epics writer
This service reads from Redis and saves the Epics PVs into H5 format. It listens on RabbitMQ (broker) for user requests.

The buffering of Epics data to Redis is implemented in the [Epics buffer](../epics_buffer/README.md) service.

## Requirements
This service needs:
- An Epics broker service (and the Redis instance that comes with it).
- A RabbitMQ instance to listen for requests.
- Docker

## Configuration
- Environment variable BROKER_HOST (default: 127.0.0.1)
- Environment variable REDIS_HOST (default: 127.0.0.1)
- Environment variable SERVICE_NAME

This service is static in the sense that once started it cannot be reconfigured. You will need to restart it with 
new parameters.

The **SERVICE_NAME** under which you start the service will be used as the **TAG** in RabbitMQ for message distribution.

## Running the service
Start the service by running the docker container:

```bash
docker run --net=host --rm  \
    --name debug.epics_writer \
    -e SERVICE_NAME=debug.epics_writer \
    -e BROKER_HOST=127.0.0.1 \
    -e REDIS_HOST=127.0.0.1 \
    paulscherrerinstitute/std-daq-service \
    epics_writer
```

Please adjust the **SERVICE\_NAME** (also docker --name flag; the docker container name should match the SERVICE_NAME).

## Monitoring

You can monitor the performance metrics of the service by running (in the host machine, while the buffer container 
is active):
```bash
docker exec -it debug.epics_writer tail -f /var/log/std-daq/perf.log
```

The output is in InfluxDB line protocol. This command can also be used to periodically read the metrics and 
send them to InfluxDB.

## Write request via RabbitMQ
The service listens on the **REQUESTS** exchange under the **TAG** specified in **SERVICE_NAME**.
The request for writing must be in format:
```json
{
  "start_pulse_id": 10000,
  "stop_pulse_id": 11000,
  "channels": ["ioc:pv1", "ioc:pv2"],
  "output_file": "/full/path/to/output.file",
  
  "metadata": {}
}
```
All fields are mandatory except **metadata**.

## Output H5 file
TODO
