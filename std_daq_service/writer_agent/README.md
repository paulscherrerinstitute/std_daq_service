# Writer agent

The writer agent is the service responsible for receiving the write commands from the broker and coordinate the stream of assembled images to the std-det-writer service, that creates the hdf5 file with the images.

```bash
usage: start.py [-h] [--broker_url BROKER_URL]
                [--log_level {CRITICAL,ERROR,WARNING,INFO,DEBUG}]
                service_name detector_name

Broker service starter.

positional arguments:
  service_name          Name of the service
  detector_name         Name of the detector to write.

optional arguments:
  -h, --help            show this help message and exit
  --broker_url BROKER_URL
                        Address of the broker to connect to.
  --log_level {CRITICAL,ERROR,WARNING,INFO,DEBUG}
                        Log level to use.
```

To start the service, from the writer_agent folder, for example:

```bash
python start.py writer_agent cSAXS.EG01V01
```
