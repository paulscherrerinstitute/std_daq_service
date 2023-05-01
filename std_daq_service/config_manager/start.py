import argparse
import logging
import os
from time import sleep

import redis
import json

_logger = logging.getLogger("ConfigManager")

# Config polling interval in seconds.
POLL_INTERVAL = 0.5


def start_manager(server_name, config_name, config_folder, redis_url):
    if not os.access(config_folder, os.W_OK):
        error_message = f"Config folder {config_folder} is not writable."
        _logger.error(error_message)
        raise RuntimeError(error_message)

    config_file = os.path.join(config_folder, f'{config_name}.json')

    redis_host, redis_port = redis_url.split(':')
    config_key = f"{config_name}:config"
    config_status_key = f"{config_name}:config_status"

    _logger.info(f"Connecting to {redis_host}:{redis_port} to save {config_file}.")

    last_seen_id = None
    redis_client = redis.Redis(host=redis_host, port=redis_port)

    while True:
        try:
            messages = redis_client.xrevrange(config_key, count=1)
            if len(messages) > 0:
                config_id = messages[0][0]
                if config_id != last_seen_id:
                    _logger.info(f"New config found: {config_id}")
                    daq_config = json.loads(messages[0][1][b'daq_config'])

                    with open(config_file, 'w') as f:
                        json.dump(daq_config, f)
                    _logger.info(f'New config downloaded: {daq_config}')

                    last_seen_id = config_id

                    redis_client.xadd(config_status_key, {"server_name": server_name, 'config_id': config_id})
                    _logger.info("Deployment completed.")

            sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            _logger.exception("Error in watcher loop.")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Configuration manager')
    parser.add_argument("server_name", type=str, help='Name of the server to deploy config to.')
    parser.add_argument("config_name", type=str, help="Name of the config to download.")
    parser.add_argument("--config_folder", default='/etc/std_daq/configs', type=str,
                        help="Folder on disk where to download the config")
    parser.add_argument('--redis_url', default="0.0.0.0:6379")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    start_manager(server_name=args.server_name, config_name=args.config_name,
                  config_folder=args.config_folder, redis_url=args.redis_url)

