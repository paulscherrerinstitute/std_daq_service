import argparse
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import run
import hashlib

from stats_logger import StatsLogger

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins=['*'], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Initialize ZMQ context (optional)
ctx = zmq.Context()
stats_logger = StatsLogger(ctx)

def validate_hash(data, received_hash, secret_key):
    data_string = json.dumps(data, sort_keys=True)
    calculated_hash = hashlib.sha256((data_string + secret_key).encode()).hexdigest()
    return calculated_hash == received_hash

# FastAPI endpoints
@app.get("/api/config/get")
async def get_configuration(config_file: str):
    logger.info(f"Fetching configuration from {config_file}")
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        logger.info(f"Successfully fetched configuration: {config}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON file: {config_file}")
        raise HTTPException(status_code=500, detail="Error decoding JSON file")

@app.post("/api/config/set")
async def update_configuration(request: Request, config_file: str, secret_key: str):
    data = await request.json()
    new_config = data["config"]
    received_hash = data["hash"]

    if not validate_hash(new_config, received_hash, secret_key):
        logger.error("Invalid hash for configuration update")
        raise HTTPException(status_code=403, detail="Invalid hash for configuration update")

    logger.info(f"Received new configuration: {new_config}")
    try:
        # Overwrite the local file
        with open(config_file, 'w') as file:
            json.dump(new_config, file, indent=4)
        logger.info(f"Successfully updated configuration file: {config_file}")
        stats_logger.log_config_change("set", "primary_server", True)
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        logger.error(f"Error writing to configuration file: {e}")
        stats_logger.log_config_change("set", "primary_server", False)
        raise HTTPException(status_code=500, detail=str(e))

def start_secondary_api(config_file, rest_port, secret_key):
    try:
        logger.info(f"Starting secondary API with config file: {config_file} on port {rest_port}")
        app.dependency_overrides[get_configuration] = lambda: config_file
        app.dependency_overrides[update_configuration] = lambda: (config_file, secret_key)
        run(app, host='0.0.0.0', port=rest_port, log_level='warning')
    except Exception as e:
        logger.exception("Error while trying to run the REST api")

def main():
    parser = argparse.ArgumentParser(description='Secondary Config Update REST interface')
    parser.add_argument("config_file", type=str, help="Path to JSON config file.")
    parser.add_argument("--rest_port", type=int, help="Port for REST api", default=5000)
    parser.add_argument("--secret_key", type=str, help="Secret key for hash validation")

    args = parser.parse_args()

    start_secondary_api(config_file=args.config_file,
                        rest_port=args.rest_port,
                        secret_key=args.secret_key)

if __name__ == "__main__":
    main()

