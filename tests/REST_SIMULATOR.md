# Standard DAQ SSR interface

Standard DAQ provides a Start Stop REST (SSR) based interface to interact with the image writer. To make it easier 
to integrate and test software against this interface we provide a simulator in the form of a Python script.

The SSR interface operates following this principles:
- The Standard DAQ is listening for detector images all the time (live stream always available).
- When the writer gets a write request it connects to the Standard DAQ and writes the next **n\_images** the detector sends.
- If the writer receives a stop request it aborts the writing after finishing to write the current image.
- Everything is designed to be operated in "Single user mode" with only one client accessing the detector at once.

## Quick start
Download and start the simulator:
```bash
curl https://raw.githubusercontent.com/paulscherrerinstitute/std_daq_service/master/tests/rest_simulator.py --output rest_simulator.py --silent
python rest_simulator.py
```
(If this does not work for you, please have a look at the [Simulator](#simulator) section below)

Request write of 2 images to /tmp/test.h5:
```bash
curl -X POST http://127.0.0.1:5000/write_sync -H "Content-Type: application/json" -d '{"n_images": 2,"output_file": "/tmp/test.h5"}'
```
Get a response when done:
```json
{
  "status":"ok",                       // Status of the request - ok == success
  "message":"Writing finished.",       // What happened in the request
  "writer":{                           // Information about the writer
    "state":"READY",                   // Current state of writer - READY == can receive another write request
    
    "acquisition":{                    // Information about the last completed acquisition
      "state":"FINISHED",              // Current state of acquisition - FINISHED == completed successfully
      
      "info":{                         // User request that generated this acquisition
        "n_images": 2,                 // Number of requested images
        "output_file": "/tmp/test.h5"},// Output file name
      
      "stats":{                        // Stats about the acquisition collected by the writer
        "n_write_completed": 2,        // Number of completed image writes
        "n_write_requested": 2,        // Number of requested image writes
        "start_time":1676844159.161408,// Start time of request as seen by writer driver
        "stop_time":1676844161.161408  // Stop time of request as seen by writer driver
}}}}
```
More information about available endpoints and request / response parameters is available below in the 
[Endpoints](#endpoints) section.

If you learn by [Examples](#examples), check the last section of this document.

## Simulator
### Requirements
In order to run the simulator you will need the following Python packages:

- Python >= 3.8
- Flask

If you are using Anaconda you can create an environment with the following commands:
```bash
conda create --name std-daq-sim python=3.8 flask
conda activate std-daq-sim
```

### Downloading the simulator
```bash
curl https://raw.githubusercontent.com/paulscherrerinstitute/std_daq_service/master/tests/rest_simulator.py --output rest_simulator.py --silent
```
### Starting the simulator
```bash
python rest_simulator.py
```

Script parameters:

```bash
usage: rest_simulator.py [-h] [--rest_port REST_PORT]

StartStop Writer REST interface

optional arguments:
  -h, --help            show this help message and exit
  --rest_port REST_PORT
                        Port for REST api
```

If you do not specify the REST_PORT, the default value of **5000** will be used. We suggest not to modify this number 
so that examples in this document will work on your instance.

## Endpoints

The base URL (if you did not modify the REST_PORT) is: **http://127.0.0.1:5000**.
The endpoint URL in the table below is a suffix to the base url.

| Name                          | Endpoint URL       | Method | Description                                       |
|-------------------------------|--------------------|--------|---------------------------------------------------|
| [Write Sync](#write-sync)     | `/write_sync`      | POST   | Request write of images and block until complete. |
| [Write Async](#write-async)   | `/write_async`     | POST   | Request write of images and return immediately.   |
| [Stop writing](#stop-writing) | `/stop`            | POST   | Stop current request.                             |
| [Get status](#get-status)     | `/status`          | GET    | Get the writer status.                            |
| [Get Config](#get-config)     | `/config`          | GET    | Get the DAQ config.                               |
| [Set Config](#set-config)     | `/config`          | POST   | Set the DAQ config.                               |

All endpoints respond with an HTTP code of 200 if no errors happened in the REST interface itself. Input errors (e.g. 
invalid file name) are not treated as errors of the REST interface. When this kind of errors happen they are 
communicated in the returned JSON.

All endpoints return the same base JSON with **status** and **message** properties:
```json
{
  "status": "ok",
  "message": "Writing started."
}
```
More information about [Base JSON properties](#base-json-properties) can be found below.

We can group endpoints into 2 categories based on the additional property they return in the response JSON:
- [Writer endpoints](#writer-endpoints) (Write Sync, Write Async, Stop writing and Get status): [writer](#writer-json-property) property that describes the state of the writer.
- [Configuration endpoints](#configuration-endpoints): (Get config, Set config): [config](#config-json-property) property that describes the current DAQ config.

Writer endpoints are used to start and stop the writer, while the configuration endpoints can be used to 
re-configure the Standard DAQ when you plan to change your detector settings (e.g. bit_depth change).

### Base JSON properties
Example:
```json
{
  "status": "error",
  "message": "Mandatory field missing: output_file"
}
```
The base JSON properties are used to communicate what happened with the users request. The **status** property is used 
as a flag to indicate if the user action was successful, while **message** describes in human language what happened.

#### status

Represents the status of the user request. Possible values:

- "ok" - user request was successful.
- "error" - user request failed.

#### message

Represents a short description of what happened - this text should mean something to the end user and can be directly 
displayed.

### Writer endpoints
Writer endpoints are used to operate the writer.

| Name                          | Endpoint URL   | Method | Use                                                              |
|-------------------------------|----------------|--------|------------------------------------------------------------------|
| [Write Sync](#write-sync)     | `/write_sync`  | POST   | Short acquisitions - request will block until writer finishes    |
| [Write Async](#write-async)   | `/write_async` | POST   | Long acquisitions - request returns immediately                  |
| [Stop writing](#stop-writing) | `/stop`        | POST   | Stop long acquisition before completion - overestimated n_images |
| [Get status](#get-status)     | `/status`      | GET    | Get the writer status - always a good one                        |

All writer endpoints return, in addition to the base JSON properties, the [writer property](#writer-json-property) that 
describes the state of the writer. Example:
```json
{
  "status":"ok",                            // User request completed successfuly
  "message":"Writer is WRITING",            // The effect of the user request was that the writer started writing
  
  "writer":{                                // Writer property
    "state":"WRITING",                      // State of the writer - currently WRITING an acquisition
    
    "acquisition":{                         // Informtion about the currently running acquisition
      "state":"ACQUIRING_IMAGES",           // Currently the images are being streamed from the camera
      
      "info":{                              // User request that generated the acquisition
        "n_images":50,                      // 50 images
        "output_file":"/tmp/test.h5"},      // To this output file
      
      "stats":{                             // Statistics about the acquisition so far
        "n_write_completed":13,             // The writer finished writing 13 images
        "n_write_requested":14,             // The writer received 14 image write requests - lagging 1 behind
        "start_time":1676846331.6930602,    // The acquisition start time as seen by the writer
        "stop_time":null                    // No stop time, acquisition still running.
}}}} 
```

#### Writer JSON property

You can see an example of the **writer** property in the [Writer endpoints](#writer-endpoints) section just above. 
This property describes the current **state** of the writer and the **acquisition** that is currently running or has last finished.
This is the core property the user should be interested in.

We have 2 properties:

- [writer/state](#writerstate) - Describes the current state of the writer: WRITING or READY.
- [writer/acquisition](#writeracquisition) - Describes the last completed or currently running acquisition.

##### writer/state
Represents the state of the writer. Possible values:

- "READY" - The writer is ready to receive the next write request.
- "WRITING" - The writer is writing. You cannot send a write request right now.

Use it as a flag to know if the writer can accept your next write request.

##### writer/acquisition
If the writer is "READY" this property will represent the last acquisition, if the writer is "WRITING" it will 
represent the currently running acquisition. Use this property to keep track of how your acquisition is going.

| Name of property                             | Description                                                                  |
|----------------------------------------------|------------------------------------------------------------------------------|
| writer/ acquisition/ state                   | State of the acquisition: FINISHED, ACQUIRING_IMAGES, FLUSHING_IMAGES, ERROR |
| writer/ acquisition/ message                 | (optional) if state == ERROR, additional information will be provided here   |
| writer/ acquisition/ info/n_images           | Number of images the user requested                                          |
| writer/ acquisition/ info/output_file        | Output file the user requested                                               |
| writer/ acquisition/ stats/n_write_completed | Number of written images                                                     |
| writer/ acquisition/ stats/n_write_requested | Number of images the writer received                                         |
| writer/ acquisition/ stats/start_time        | Start time of writing                                                        |
| writer/ acquisition/ stats/stop_time         | (can be null) Stop time of writing                                           |

#### Write Sync
Start an acquisition and block the REST call until the acquisition is completed. This is most useful for short 
acquisitions, say up to 30 seconds. The positive side of using this endpoint is that everything is very simple - one 
REST request, one output file. The negative side is that you are not able to get updates on how the acquisition is 
going until it finishes. If this is not interactive enough (e.g. you need live performance statistics or your 
acquisitions are longer than cca. 30 seconds) we suggest the [Write Async](#write-async) endpoint.

| Attribute     | Value                                                                             |
|---------------|-----------------------------------------------------------------------------------|
| URL           | /write_sync                                                                       |
| HTTP Method   | POST                                                                              |
| Request JSON  | {<br/>"n_images": 2, <br/>"output_file": "/tmp/test.h5"<br/>}                      |
| Description   | Start a new acquisition and complete the REST call when the acquisition finishes. |
| Response JSON | [Writer JSON property](#writer-json-property)                                     |

##### Request JSON
The request JSON represents the information needed to start an acquisition. Example:
```json
{
  "n_images": 2,                  // Write 2 images
  "output_file": "/tmp/test.h5"   // To this file.
}
```

- n_images: number of images to acquire. Must be an unsigned 32 bit integer, greater than 0.
- output_file: full posix path of the output filename. Example: "/gpfs/experiment/acq_02.h5". Relative paths not allowed.

Example usage with Curl:
```bash
curl -X POST http://127.0.0.1:5000/write_sync -H "Content-Type: application/json" -d '{"n_images": 2,"output_file": "/tmp/test.h5"}'
```

Example usage with Python:
```python
import requests
json_data = {"n_images":2, "output_file":"/tmp/test.h5"}
response = requests.post(url = "http://127.0.0.1:5000/write_sync", json=json_data)
print(response.json())
```

#### Write Async
Start an acquisition and return as soon as the writer starts writing. You are now free to do other things. If you are 
interested in how your acquisition is going, you will have to use the [Get Status](#get-status) endpoint. If you want to 
terminate your acquisition before it collected the pre-set number of images use the [Stop writing](#stop-writing) endpoint.

| Attribute     | Value                                                                                     |
|---------------|-------------------------------------------------------------------------------------------|
| URL           | /write_async                                                                              |
| HTTP Method   | POST                                                                                      |
| Request JSON  | {<br/>"n_images": 200, <br/>"output_file": "/tmp/test.h5"<br/>}                            |
| Description   | Start a new acquisition and complete the REST call when the writers create an empty file. |
| Response JSON | [Writer JSON property](#writer-json-property)                                             |

[The request JSON](#request-json) is the same as in the Write Sync endpoint.

Example usage with Curl:
```bash
curl -X POST http://127.0.0.1:5000/write_async -H "Content-Type: application/json" -d '{"n_images": 200,"output_file": "/tmp/test.h5"}'
```

Example usage with Python:
```python
import requests
json_data = {"n_images":200, "output_file":"/tmp/test.h5"}
response = requests.post(url = "http://127.0.0.1:5000/write_async", json=json_data)
print(response.json())
```

#### Stop writing
Stop the current acquisition. This can be used if we selected too many images in the **n\_images** request parameter.
Usually used with [Write Async](#write-async) and [Get status](#get-status) endpoints.

| Attribute     | Value                                         |
|---------------|-----------------------------------------------|
| URL           | /stop                                         |
| HTTP Method   | POST                                          |
| Description   | Stop the current acquisition.                 |
| Response JSON | [Writer JSON property](#writer-json-property) |

Example usage with Curl:
```bash
curl -X POST http://127.0.0.1:5000/stop
```

Example usage with Python:
```python
import requests
response = requests.post(url = "http://127.0.0.1:5000/stop")
print(response.json())
```

#### Get status
Return the status of the writer. The most useful command of them all. Call this endpoint to know if the writer is ready 
for your next write request.

| Attribute     | Value                                         |
|---------------|-----------------------------------------------|
| URL           | /status                                       |
| HTTP Method   | GET                                           |
| Description   | Return current status of writer.              |
| Response JSON | [Writer JSON property](#writer-json-property) |

Example usage with Curl:
```bash
curl http://127.0.0.1:5000/status
```

Example usage with Python:
```python
import requests
response = requests.get(url = "http://127.0.0.1:5000/status")
print(response.json())
```

### Configuration endpoints
The configuration endpoints can be used to re-configure the Standard DAQ when you plan to change your 
detector settings. Your detector should not be sending images to the standard DAQ when you execute this procedure. 
Changing configuration can take up to 30 seconds, based on the complexity of your deployment and the current 
deployment system load.

| Name                          | Endpoint URL | Method | Use                                 |
|-------------------------------|--------------|--------|-------------------------------------|
| [Get Config](#get-config)     | `/config`    | GET    | Get the Standard DAQ configuration. |
| [Set Config](#set-config)     | `/config`    | POST   | Set the Standard DAQ configuration. |

All configuration endpoints return, in addition to the base JSON properties, the [config property](#config-json-property) that 
describes the Standard DAQ configuration. Example:
```json
{
  "status":"ok",                                  // User request completed successfully.
  "message":"DAQ configured for bit_depth=32.",   // The most important message for the user.

  "config":{                                      // Config property
    "bit_depth":32,                               // Detector bit depth
    "detector_name":"Eiger9M",                    // Detector name
    "detector_type":"eiger",                      // Detector type
    "image_pixel_height":2016,                    // Image height in pixels
    "image_pixel_width":2016,                     // Image width in pixels
    "n_modules":72,                               // Number of module in the detector.
    "start_udp_port":2000                         // Start UDP port of the first module.
}}
```

#### Config JSON property
You can see an example of the **config** property in the [Configuration endpoints](#configuration-endpoints) section just above. 

| Name of property           | Description                                          |
|----------------------------|------------------------------------------------------|
| config/ bit_depth          | Bit depth of the detector image. Detector dependent. |
| config/ detector_name      | Name of the detector to acquire.                     |
| config/ detector_type      | Type of the detector to acquire.                     |
| config/ image_pixel_height | Expected image height in pixels.                     |
| config/ image_pixel_width  | Expected image width in pixels.                      |
| config/ n_modules          | Number of modules the detector has.                  |
| config/ start_udp_port     | Udp port of first module.                            |

In most cases you will only be interested in the **bit_depth** field, and even then only if your detector 
allows to change this setting.

#### Get config
Return the current Standard DAQ config.

| Attribute     | Value                                         |
|---------------|-----------------------------------------------|
| URL           | /config                                       |
| HTTP Method   | GET                                           |
| Description   | Return current configuration of Standard DAQ. |
| Response JSON | [Config JSON property](#config-json-property) |

Example usage with Curl:
```bash
curl http://127.0.0.1:5000/config
```

Example usage with Python:
```python
import requests
response = requests.get(url = "http://127.0.0.1:5000/config")
print(response.json())
```

#### Set config
Re-configures Standard DAQ with a new config. Changing configuration can take up to 30 seconds, based on the 
complexity of your deployment and the current deployment system load. This REST call will block until the 
configuration is applied to the system.

| Attribute      | Value                                         |
|----------------|-----------------------------------------------|
| URL            | /config                                       |
| HTTP Method    | POST                                          |
| Request JSON   | [Config JSON property](#config-json-property) |
| Description    | New Standard DAQ config.                      |
| Response JSON  | [Config JSON property](#config-json-property) |

The **Request JSON** does not need to contain all the fields - just the one that change. For example if we only 
want to change bit_depth, our Request JSON would be:
```json
{
  "bit_depth": 16
}
```

Example usage with Curl:
```bash
curl -X POST http://127.0.0.1:5000/config -H "Content-Type: application/json" -d '{"bit_depth": 16}'
```

Example usage with Python:
```python
import requests
json_data = {"bit_depth": 16}
response = requests.post(url = "http://127.0.0.1:5000/config", json=json_data)
print(response.json())
```

## Examples
Start the simulator. Please check the [Simulator](#simulator) section for more info.

Some highlights:
- **output\_file** must be an absolute path.
- **n\_images** must be an integer larger than 0.
- Do not send images from the detector when changing Standard DAQ config.
- Changing config can take up to 30 seconds depending on your setup and deployment system load.

### Get current writer status

```bash
curl http://127.0.0.1:5000/status
```

### Collect 100 images the easiest way

```bash
curl -X POST http://127.0.0.1:5000/write_sync -H "Content-Type: application/json" -d '{"n_images": 100,"output_file": "/tmp/test.h5"}'
```

### Change Standard DAQ bit_depth configuration

```bash
curl -X POST http://127.0.0.1:5000/config -H "Content-Type: application/json" -d '{"bit_depth": 16}'
```

### Stop currently running acquisition

```bash
curl -X POST http://127.0.0.1:5000/stop
```