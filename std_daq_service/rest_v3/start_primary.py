import argparse
import json
import logging
from jsonschema import validate, ValidationError
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import run
from time import time
import requests
import hashlib

from stats_logger import StatsLogger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JSON Schema for validation
JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "detector_name": {"type": "string"},
        "detector_type": {"type": "string"},
        "n_modules": {"type": "integer"},
        "bit_depth": {"type": "integer"},
        "image_pixel_height": {"type": "integer"},
        "image_pixel_width": {"type": "integer"},
        "start_udp_port": {"type": "integer"},
        "writer_user_id": {"type": "integer"},
        "submodule_info": {"type": "object"},
        "max_number_of_forwarders_spawned": {"type": "integer"},
        "use_all_forwarders": {"type": "boolean"},
        "module_sync_queue_size": {"type": "integer"},
        "module_positions": {"type": "object"}
    },
    "required": ["detector_name", "detector_type", "n_modules", "bit_depth", "image_pixel_height", "image_pixel_width", "start_udp_port", "writer_user_id", "submodule_info", "max_number_of_forwarders_spawned", "use_all_forwarders", "module_sync_queue_size", "module_positions"]
}

# FastAPI app initialization
app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins=['*'], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Initialize ZMQ context (optional)
ctx = zmq.Context()
stats_logger = StatsLogger(ctx)

def generate_hash(data, secret_key):
    data_string = json.dumps(data, sort_keys=True)
    return hashlib.sha256((data_string + secret_key).encode()).hexdigest()

# FastAPI endpoints
@app.get("/api/config/get")
async def get_configuration(config_file: str, user: str):
    start_time = time()
    logger.info(f"User {user} fetching configuration from {config_file}")
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        duration = time() - start_time
        logger.info(f"User {user} successfully fetched configuration in {duration:.2f} seconds")
        stats_logger.log_config_change("get", user, True)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        stats_logger.log_config_change("get", user, False)
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON file: {config_file}")
        stats_logger.log_config_change("get", user, False)
        raise HTTPException(status_code=500, detail="Error decoding JSON file")

@app.post("/api/config/set")
async def update_configuration(request: Request, config_file: str, user: str, secondary_server: str, secret_key: str):
    start_time = time()
    new_config = await request.json()
    logger.info(f"User {user} received new configuration: {new_config}")
    try:
        validate(instance=new_config, schema=JSON_SCHEMA)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        stats_logger.log_config_change("set", user, False)
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # Overwrite the local file
        with open(config_file, 'w') as file:
            json.dump(new_config, file, indent=4)
        duration = time() - start_time
        logger.info(f"User {user} successfully updated configuration in {duration:.2f} seconds")
        stats_logger.log_config_change("set", user, True)

        # Generate hash for the configuration
        config_hash = generate_hash(new_config, secret_key)

        # Send updated configuration to the secondary server
        response = requests.post(f"{secondary_server}/api/config/set", json={"config": new_config, "hash": config_hash})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to synchronize with the secondary server")

        return {"message": "Configuration updated and synchronized successfully"}
    except Exception as e:
        logger.error(f"Error writing to configuration file: {e}")
        stats_logger.log_config_change("set", user, False)
        raise HTTPException(status_code=500, detail=str(e))

def start_api(config_file, rest_port, secondary_server, secret_key):
    try:
        logger.info(f"Starting API with config file: {config_file} on port {rest_port}")
        app.dependency_overrides[get_configuration] = lambda: config_file
        app.dependency_overrides[update_configuration] = lambda: (config_file, secondary_server, secret_key)
        run(app, host='0.0.0.0', port=rest_port, log_level='warning')
    except Exception as e:
        logger.exception("Error while trying to run the REST api")

def main():
    parser = argparse.ArgumentParser(description='Standard DAQ Start Stop REST interface')
    parser.add_argument("config_file", type=str, help="Path to JSON config file.")
    parser.add_argument("--rest_port", type=int, help="Port for REST api", default=5000)
    parser.add_argument("--secondary_server", type=str, help="Address of the secondary server for synchronization")
    parser.add_argument("--secret_key", type=str, help="Secret key for hash generation")

    args = parser.parse_args()

    start_api(config_file=args.config_file,
              rest_port=args.rest_port,
              secondary_server=args.secondary_server,
              secret_key=args.secret_key)

if __name__ == "__main__":
    main()

