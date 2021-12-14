# SLS Rest interface

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
