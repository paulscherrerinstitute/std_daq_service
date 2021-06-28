# sf_daq_service

This is a monorepo for std daq services.

## Architecture overview
An std-daq-service is a micro service that uses **RabbitMQ** for message passing and **ZMQ** for data 
streams. The services are built using predefined formats and standard in order to make them compatible 
with the rest of the std-daq.

The std-daq is composed by two event flows:

- Detector data flow (uses ZMQ for communication)
- User interaction flow (Uses RabbitMQ for communication)

## Detector image flow

![Detector data flow](docs/detector_data_flow.jpg)

In order from the detector onward, the main components involved into this flow are:

- Detector readout (receive detector and assemble images)
- Detector buffer (buffer images and transfer them to other servers)
- Detector writer (write assembled images from buffer to disk)

### Detector readout
The goal of this component is to convert the raw detector frames received via UDP into final images. It transforms 
the detector into a generic camera. By unifying all detectors into the same generic cameras we can reuse the 
pipelines developed for one detector by many, which allows us to offer centralized services to beamlines.

In order to achieve this it must first receive the UDP packets from the detector in **std\_udp\_recv**,
reconstruct the frames and save them into the FrameBuffer. The frames from all modules are then synchronized into 
a single metadata stream sent to **std\_assembler**.

The **std\_assembler** takes care of image conversion (background, pedestal, corrections etc.) and assembly of the modules 
into the desired shape. Once the final images are ready, they are saved into the **DetectorBuffer** and a stream of 
**ImageMetadata** is sent out to anyone listening.

### Detector buffer
TODO

### Detector writer
TODO

## User interaction path
TODO

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

## Deployment

The deployment can only be made with Docker images. You must copy a specific version of the software into 
a new version of the **std-daq-service** docker image and push it to the registry. The **std-daq-service**
image you build must use the image **std-daq-service-base** base.

### Building the image base

Building the base image should not be necessary unless you are trying to update the std-daq platform. If 
you are not sure what this means, please do not perform this step.

Navigate to **docker/** and run 
```bash
./build_std-daq-service-base.sh
```

### Building the service image

TODO: