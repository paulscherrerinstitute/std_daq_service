# Start Stop REST interface simulator

This flask-based REST proxy service simulates the std-daq and can be used to integrate and test your std-daq interface.

## Requirements

In order to run the simulator you will need the following Python packages:

- Python >= 3.8
- Flask

If you are using Anaconda you can create an environment with the following commands:
```bash
conda create --name std-daq-sim python=3.8 flask
conda activate std-daq-sim
```

## Starting the REST interface

Script parameters:

```bash
usage: rest_simulator.py [-h] [--rest_port REST_PORT]

StartStop Writer REST interface

optional arguments:
  -h, --help            show this help message and exit
  --rest_port REST_PORT
                        Port for REST api
```

If you do not specify the REST_PORT, the default value of 5000 will be used. We suggest not to modify this port 
so the examples below will work.

To start the service run:

```bash
python rest_simulator.py
```

## Endpoints

The base URL (if you did not modify the REST_PORT) is: **http://127.0.0.1:5000**.
The endpoint URL in the table below is a suffix to the base url.

| Endpoint URL   | Method | Description                                       |
|----------------|--------|---------------------------------------------------|
| `/write_sync`  | POST   | Request write of images and block until complete. |
| `/write_async` | POST   | Request write of images and return immediatly.    |
| `/stop`        | POST   | Stop current request.                             |
| `/status`      | GET    | Get the writer status.                            |
| `/config`      | GET    | Get the DAQ config.                               |
| `/config`      | POST   | Set the DAQ config.                               |




### /write_sync (POST)
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