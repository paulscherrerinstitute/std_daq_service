# Standard DAQ client

Python client for accessing the REST api. Provides also command line tools for the same purpose.

## Getting started

### Python client

```python
from std_daq_client import StdDaqClient
rest_server_url = 'http://localhost:5000'
client = StdDaqClient(url_base=rest_server_url)

client.get_status()
```

### CLI interface

- std_cli_get_status
- std_cli_get_config
- std_cli_get_logs
- std_cli_get_stats
- std_cli_get_deploy_status