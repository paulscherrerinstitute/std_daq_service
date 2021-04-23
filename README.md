# sf_daq_service

This is a monorepo for sf-daq services.

## Running the tests

In order to run all the tests you need to have a local 
instance of RabbitMQ running. You can just start a 
docker container for this:

```bash
docker run -d --name sf-msg-broker -p 15672:15672 -p 5672:5672 rabbitmq:3-management
```

You have 2 ports mapped:

- 15672 is the management console. You can access it via browser at [http://localhost:15672](http://localhost:15672)
the user is **guest** and password is **guest**.
- 5672 is the broker address. 