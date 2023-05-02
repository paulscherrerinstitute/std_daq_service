import argparse
import logging
import os
from time import sleep

import redis
import json

from std_daq_service.rest_v2.redis import StdDaqRedisStorage

_logger = logging.getLogger("ConfigManager")

# Config polling interval in seconds.
POLL_INTERVAL = 0.5
LAST_DEPLOYED_CONFIG_FILENAME = 'LAST_DEPLOYED_CONFIG_ID'

def start_manager(server_name, config_file, redis_url):
    config_folder = os.path.dirname(config_file)
    if not os.access(config_folder, os.W_OK):
        error_message = f"Config folder {config_folder} is not writable."
        _logger.error(error_message)
        raise RuntimeError(error_message)

    last_seen_id = None
    last_deployed_config_filename = config_folder + LAST_DEPLOYED_CONFIG_FILENAME
    if os.path.exists(config_folder + LAST_DEPLOYED_CONFIG_FILENAME):
        with open(last_deployed_config_filename, 'r') as input_file:
            last_seen_id = input_file.read()
            _logger.info(f"Deployment record found. Last deployed config_if {last_seen_id}")

    redis_host, redis_port = redis_url.split(':')
    _logger.info(f"Connecting to {redis_host}:{redis_port} to save {config_file}.")
    redis_client = redis.Redis(host=redis_host, port=redis_port)

    storage = StdDaqRedisStorage(redis=redis_client, redis_namespace=config_file)

    while True:
        try:
            config_id, daq_config = storage.get_config()

            if config_id is not None and config_id != last_seen_id:


                _logger.info(f"Deploying new config: {daq_config}")
                storage.set_deployment_status(config_id=config_id,
                                              server_name=server_name,
                                              message="Deploying")

                with open(config_file, 'w') as f:
                    json.dump(daq_config, f)

                storage.set_deployment_status(config_id=config_id,
                                              server_name=server_name,
                                              message='Done')

                _logger.info("Deployment completed.")
                last_seen_id = config_id

            sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception:
            _logger.exception("Error in watcher loop.")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Configuration manager')
    parser.add_argument("server_name", type=str, help='Name of the server for deployment status reporting.')
    parser.add_argument("config_file", type=str, help="Path to the config file managed by this instance.")
    parser.add_argument("--config_folder", default='/etc/std_daq/configs', type=str,
                        help="Folder on disk where to download the config")
    parser.add_argument('--redis_url', default="0.0.0.0:6379")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    start_manager(server_name=args.server_name, config_file=args.config_file, redis_url=args.redis_url)
