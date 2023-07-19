import argparse
import json
import logging

import zmq
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.client import Redis
from uvicorn import run

from std_daq_service.config import load_daq_config, get_stream_addresses
from std_daq_service.rest_v2.daq import DaqRestManager
from std_daq_service.rest_v2.logs import LogsLogger
from std_daq_service.rest_v2.mjpeg import MJpegLiveStream
from std_daq_service.rest_v2.redis_storage import StdDaqRedisStorage
from std_daq_service.rest_v2.stats import StatsLogger
from std_daq_service.writer_driver.writer_driver import WriterDriver
from std_daq_service.rest_v2.writer import WriterRestManager, StatusLogger
from std_daq_service.rest_v2.rest import register_rest_interface


_logger = logging.getLogger(__name__)


def start_api(config_file, rest_port, sim_url_base, redis_url, live_stream_url):
    writer_manager = None
    ctx = None
    status_logger = None
    stats_logger = None
    logs_logger = None

    try:
        _logger.info(f'Starting Start Stop REST for file: {config_file} (rest_port={rest_port}).')

        daq_config = load_daq_config(config_file)
        detector_name = daq_config['detector_name']

        command_address, in_status_address, out_status_address, image_metadata_address = \
            get_stream_addresses(detector_name)

        redis_host, redis_port = redis_url.split(':')
        _logger.info(f"Connecting to Redis {redis_host}:{redis_port}")
        redis = Redis(host=redis_host, port=redis_port)
        storage = StdDaqRedisStorage(redis)

        # If the current config file is not in Redis - cold deploy, first time run.
        # This will cause a deploy of the config.
        config_id, _ = storage.get_config()
        if config_id is None:
            _logger.info("No config present in storage. Re-deploying config.")
            storage.set_config(daq_config)

        app = FastAPI()
        app.add_middleware(CORSMiddleware,
                           allow_origins=['*'], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

        ctx = zmq.Context()

        writer_driver = WriterDriver(ctx, command_address, in_status_address, out_status_address,
                                     image_metadata_address)
        writer_manager = WriterRestManager(writer_driver=writer_driver)

        status_logger = StatusLogger(ctx=ctx, storage=storage, writer_status_url=out_status_address)
        stats_logger = StatsLogger(ctx, storage=storage, image_stream_url=image_metadata_address,
                                   writer_status_url=out_status_address)
        logs_logger = LogsLogger(ctx, writer_driver.out_status_address, storage)

        daq_manager = DaqRestManager(storage=storage)

        mjpeg_streamer = MJpegLiveStream(ctx, live_stream_url=live_stream_url)
        register_rest_interface(app, writer_manager=writer_manager, daq_manager=daq_manager, sim_url_base=sim_url_base,
                                streamer=mjpeg_streamer, storage=storage)

        run(app, host='0.0.0.0', port=rest_port, log_level='warning')

    except Exception as e:
        _logger.exception("Error while trying to run the REST api")

    except KeyboardInterrupt:
        _logger.info("Starting shutdown procedure.")

    finally:

        if writer_manager:
            writer_manager.close()

        if status_logger:
            status_logger.close()
        if stats_logger:
            stats_logger.close()
        if logs_logger:
            logs_logger.close()

        if ctx:
            ctx.destroy()

    _logger.info("Start Stop REST properly shut down.")


def main():
    parser = argparse.ArgumentParser(description='Standard DAQ Start Stop REST interface')
    parser.add_argument("config_file", type=str, help="Path to JSON config file.")
    parser.add_argument("--rest_port", type=int, help="Port for REST api", default=5000)
    parser.add_argument("--sim_url_base", type=str, default='http://localhost:5001',
                        help="URL to control the simulation")
    parser.add_argument('--redis_url', default="0.0.0.0:6379", help="Redis management instance")
    parser.add_argument('--live_stream_url', default="tcp://127.0.0.1:20000", help="Live stream url for MJPEG streamer")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    start_api(config_file=args.config_file,
              rest_port=args.rest_port,
              sim_url_base=args.sim_url_base,
              redis_url=args.redis_url,
              live_stream_url=args.live_stream_url)


if __name__ == "__main__":
    main()
