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
into the desired shape. Once the final images are ready, they are saved into the **ImageBuffer** and a stream of 
**ImageMetadata** is sent out to anyone listening.

### Detector buffer
The detector buffer provides a RAM image buffering structure (**ImageBuffer**) and buffer transfer services 
(**std\_stream\_send** and **std\_stream\_recv**) that can be used to transfer this RAM buffering structure to and 
from other servers. The goal of this component is to provide a detector image buffer that can be replicated across 
multiple servers and that allows applications running on the same server to access the detector images without 
additional memory copies.

It defines the **ImageMetadata** stream structure that needs to be implemented by any component that wants to 
communicate directly with the buffer.

The **std_stream_recv** broadcasts the metadata of received images in the same way as the **std\_assembler** does
in the **Detector readout** component, making them interchangeable for std-daq-services.

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