# sf_daq_service

This is a monorepo for sf-daq services.

## Running the tests

In order to run all the tests you need to have a local 
instance of RabbitMQ running. You can just start a 
docker container for this:

```bash
docker run -d --hostname sf-msg-broker --name sf-msg-broker --net=host rabbitmq:3-management
```