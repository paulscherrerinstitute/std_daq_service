# std_daq_service

This is a monorepo for standard daq services.

Documentation of individual services:
- [Epics buffer](std_daq_service/epics_buffer/README.md)
- [Epics writer](std_daq_service/epics_writer/README.md)

## Getting started

### Setup development environment
For development and testing you need to have **Docker** and **docker-compose** installed. You must run 
Redis and RabbitMQ in order to run unit tests. To start them, from the root folder of the project, execute:
```bash
sh setup_dev_env.sh
```
This will bring up both services on your local machine and populate Redis with test configurations 
(located in **tests/redis\_configs/\[service\_name\].json**). You can now execute the unit tests from your local 
dev environment or you can use the provided docker container.

You can also manually setup your local paths (if your IDE does not do that already) by running:
```bash
python setup.py develop
```

### Running unit tests
To run the tests in a docker container, execute from the root of the project:
```bash
sh tests_in_docker.sh
```
(Please note that at the moments the test container uses host networking, so you might have problems on a Mac - 
you will need to open the needed ports manually.)

If you have set your development environment correctly you can also run the unit tests from your machine. 
In the root folder run:
```bash
python -m unittest discover tests/
```

### Starting a service
Once you have Redis and RabbitMQ running locally you can start the services straight from your machine, but we 
suggest you use the provided docker container for this. 

To run services in the docker container, from the project root:
```bash 
docker run --net=host --rm  \
    -e SERVICE_NAME=debug.epics_buffer \
    -v $(pwd)/tests/redis_configs/debug.epics_buffer.json:/std_daq_service/config.json \
    paulscherrerinstitute/std-daq-service \
    epics_buffer
```

For more information on the parameters of the docker container please check the **Service container** section. 

### Service container
Extended documentation: [Service container](docker/README.md)

TODO: Add more info about the service container

## Deployment

The deployment should be made with Docker images. You must copy a specific version of the software into 
a new version of the **std-daq-service** docker image and push it to the registry. The **std-daq-service**
image you build must use the image **std-daq-service-base** base.

If you modified the 

## Architecture overview
An std-daq-service is a micro service that uses **RabbitMQ** for interaction with users and **ZMQ** for data 
streams. The services are built using predefined formats and standard in order to make them part of the 
std-daq platform.

The std-daq is composed by two event flows:

- Detector data flow (images transfer, uses ZMQ for communication)
- User interaction flow (transfer of user requests, uses RabbitMQ for communication)

## Detector data flow

![Detector data flow](docs/detector_data_flow.jpg)

In order from the detector onward, the 3 components involved into this flow are:

- Detector readout (receive detector modules and assemble final images)
- Detector buffer (buffer images and transfer images to other servers)
- Detector writer (write images from buffer to disk)

### Detector readout
The goal of this component is to convert the raw detector frames received via UDP into final images. It transforms 
the detector into a generic camera. By having all detectors standardized on the same interface we can have a common 
std-daq for all PSI facilities.  

In order to achieve this the component must first receive the UDP packets from the detector in **std\_udp\_recv**,
reconstruct the frames and save them into **FrameBuffer**. The frames from all modules are then synchronized into 
a single metadata stream message of **RawMetadata** format that is sent to **std\_assembler**.

The **std\_assembler** takes care of image conversion (background, pedestal, corrections etc.) and assembly of the modules 
into the desired shape. Once the final images are ready, they are saved into the **ImageBuffer** and a stream of 
**ImageMetadata** is sent out to anyone listening.

### Detector buffer
The detector buffer provides a RAM image buffering structure (**ImageBuffer**) and buffer transfer services 
(**std\_stream\_send** and **std\_stream\_recv**) that can be used to transfer the RAM buffering structure to and 
from other servers. The goal of this component is to provide a detector image buffer that can be replicated across 
multiple servers and that allows applications running on the same server to access the detector images without 
additional memory copies.

It defines the **ImageMetadata** stream structure that needs to be implemented by any component that wants to 
communicate operate directly with the buffer.

The **std_stream_recv** broadcasts the metadata of received images in the same way as the **std\_assembler** does
in the **Detector readout** component. Because of this detector image buffer replication is transparent to std-daq-services.

### Detector writer
This is the first component so far that we can call a **std-daq-service**. On one end it connects to the 
**std\_assembler** to receive a stream of the latest assembled images and on the other end it listens to the broker
for write requests from the users. When requested by the user, the images are writen from ram buffer to disk 
without additional copies. 

Internally this component uses a **StoreStream** that controls the behaviour of the writer. The component is made 
up from 2 parts:

- **writer\_agent** (Listens to RabbitMQ for writing requests, executes the request by forwarding 
the **ImageMetadata** stream encapsulated into **StoreStream** format to the **std\_h5\_writer**)
- **std\_h5\_writer** (Receives a stream of **StoreStream** format and writes images from **ImageBuffer** to H5 file.)

#### H5 File format

TODO

## Rest

The flask-based rest proxy service interacts with the broker and allows to trigger commands to the writer agent based on a ```service_tag``` and ```tag```. 

```bash
usage: start.py [-h] [--broker_url BROKER_URL]
                [--log_level {CRITICAL,ERROR,WARNING,INFO,DEBUG}]
                service_name tag

Rest Proxy Service

positional arguments:
  service_name          Name of the service
  tag                   Tag on which the proxy listens to statuses and sends
                        requests.

optional arguments:
  -h, --help            show this help message and exit
  --broker_url BROKER_URL
                        Address of the broker to connect to.
  --log_level {CRITICAL,ERROR,WARNING,INFO,DEBUG}
                        Log level to use.
```

To start the service, from the rest folder, for example:

```bash
python start.py rest eiger
```

---
**NOTE**

The STD DAQ rest server uses the [slsdet package](https://anaconda.org/slsdetectorgroup/slsdet) to set and get configurations to the detector. The currently covered subset of parameters are: triggers, timing, frames, period, exptime, dr, speed, tengiga and threshold.

---

### Usage examples

#### /write_sync (POST)
Triggers a synchronous write command to the writer agent.

```python
data = {"sources":"eiger", "n_images":10, "output_file":"/tmp/test.h5"}
headers = {'Content-type': 'application/json'}
r = requests.post(url = "http://127.0.0.1:5000/write_sync", json=data, headers=headers)
```

```bash
curl -X POST http://127.0.0.1:5000/write_sync -H "Content-Type: application/json" -d '{"n_images":5,"output_file":"/tmp/test.h5", "sources":"eiger"}'
```

Rest service answer:

```bash
{"request_id":"dd33c54f-2d61-4da4-96fd-c4012d75c797","response":{"end_timestamp":1627898407.391828,"init_timestamp":1627898398.259257,"output_file":"/tmp/test.h5","status":"request_success"}}
```

#### /write_async (POST)
Triggers an asynchronous write command to the writer agent.

```python
data = {"sources":"eiger", "n_images":10, "output_file":"/tmp/test.h5"}
headers = {'Content-type': 'application/json'}
r = requests.post(url = "http://127.0.0.1:5000/write_async", json=data, headers=headers)
```

```bash
curl -X POST http://127.0.0.1:5000/write_async -H "Content-Type: application/json" -d '{"n_images":5,"output_file":"/tmp/test.h5", "sources":"eiger"}'
```

Rest service answer:

```bash
{"request_id":"5b50509f-e441-4f9a-8031-de10eceab9d6"}
```

#### /write_kill (POST)
Kills an ongoing acquisition based on its ```request_id```.

```python
# triggers an async acquisition
data = {"sources":"eiger", "n_images":10, "output_file":"/tmp/test.h5"}
headers = {'Content-type': 'application/json'}
r = requests.post(url = "http://127.0.0.1:5000/write_async", json=data, headers=headers)
time.sleep(3)
# stores the request_id from the write_async post and kills it
req_id = str(r.json()["request_id"])
data = {"request_id":req_id}
headers = {'Content-type': 'application/json'}
r = requests.post(url = "http://127.0.0.1:5000/write_kill", json=data, headers=headers)
```

Rest service answer:

```bash
{"request_id":"88fb758a-827b-4533-bbdc-d4b68c4f410a","response":{"end_timestamp":1627908976.427919,"init_timestamp":1627908973.337146,"output_file":"/tmp/test.h5","status":"request_success"}}
```

### Eiger configuration set (POST)

```python
data = {"det_name":"eiger","config":{"frames":5,"dr":32}}
headers = {'Content-type': 'application/json'}
r = requests.post(url = "http://127.0.0.1:5000/detector", json=data, headers=headers)
```

Rest service answer:

```bash
{'response': 'request_success'}
```

---
**NOTE**

When a parameter is not recognized the expected response is: 

```bash
{'response': 'Parameter not valid: <NAME_OF_NOT_VALID_PARAM>'}
```

---



### Eiger configuration get (GET)
Gets the eiger detector configuration

```python
r = requests.get(url = "http://127.0.0.1:5000/detector/eiger")
```

Rest service answer:

```bash
{'det_name': 'EIGER', 'dr': 16, 'exptime': 1.0, 'frames': 100, 'period': 0.01, 'speed': 'speedLevel.FULL_SPEED', 'tengiga': True, 'threshold': -1, 'timing': 'timingMode.AUTO_TIMING', 'triggers': 1}
```

## Writer Agent

The writer agent is the service responsible for receiving the write commands from the broker and coordinate the stream of assembled images to the std-det-writer service, that creates the hdf5 file with the images.

```bash
usage: start.py [-h] [--broker_url BROKER_URL]
                [--log_level {CRITICAL,ERROR,WARNING,INFO,DEBUG}]
                service_tag service_name detector_name

Broker service starter.

positional arguments:
  service_tag           Where to bind the service
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
python start.py eiger writer_agent cSAXS.EG01V01
```




## User interaction flow
![User interaction flow](docs/user_interaction_flow.jpg)

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



