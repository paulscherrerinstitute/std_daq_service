import json
import logging
import os
import uuid

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_CONFIG_FILE = 'config.json'


def default_service_setup(parser):

    parser.add_argument("--service_name", type=str, default=os.environ.get("SERVICE_NAME", uuid.uuid4()),
                        help="Name of the service. If not specified, env variables "
                             "SERVICE_NAME will be used. Otherwise random.")
    parser.add_argument("--json_config_file", type=str, default=DEFAULT_CONFIG_FILE, help="Path to JSON config file.")
    parser.add_argument("--log_level", default=DEFAULT_LOG_LEVEL,
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level,
                        format="%(levelname)s %(asctime)s %(name)s %(message)s")

    # Suppress pika logging
    logging.getLogger("pika").setLevel(logging.WARNING)

    with open(args.json_config_file, 'r') as input_file:
        config = json.load(input_file)

    return args.service_name, config, args
