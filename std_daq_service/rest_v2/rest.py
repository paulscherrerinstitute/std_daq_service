import os
from io import BytesIO
from logging import getLogger
from typing import Optional

import cv2
import numpy as np
import requests
from starlette.responses import FileResponse, JSONResponse, StreamingResponse

from std_daq_service.rest_v2.redis_storage import StdDaqRedisStorage
from std_daq_service.rest_v2.rest_models import WriterResponse, SimulatorResponse, ConfigResponse, StatsResponse, \
    LogsResponse, DeploymentStatusResponse, ConfigRequest, WriteRequest
from std_daq_service.udp_simulator.start_rest import STATUS_ENDPOINT, START_ENDPOINT, STOP_ENDPOINT
from std_daq_service.rest_v2.daq import DaqRestManager
from std_daq_service.rest_v2.utils import validate_output_file
from std_daq_service.rest_v2.writer import WriterRestManager
from fastapi.staticfiles import StaticFiles

# TODO: Separate the drivers based on the REST namespace.
WRITER_WRITE_SYNC_ENDPOINT = "/writer/write_sync"
WRITER_WRITE_ASYNC_ENDPOINT = "/writer/write_async"
WRITER_STATUS_ENDPOINT = "/writer/status"
WRITER_STOP_ENDPOINT = "/writer/stop"

SIM_STATUS_ENDPOINT = '/simulation' + STATUS_ENDPOINT
SIM_START_ENDPOINT = '/simulation' + START_ENDPOINT
SIM_STOP_ENDPOINT = '/simulation' + STOP_ENDPOINT

DAQ_LIVE_STREAM_ENDPOINT = '/daq/live'
DAQ_CONFIG_ENDPOINT = '/daq/config'
DAQ_STATS_ENDPOINT = '/daq/stats'
DAQ_LOGS_ENDPOINT = '/daq/logs/{n_logs}'
DAQ_DEPLOYMENT_STATUS_ENDPOINT = '/daq/deployment'

FILE_METADATA = '/file/{acquisition_id}'
FILE_IMAGE = '/fileview/{acquisition_id}/{i_image}'

request_logger = getLogger('request_log')
_logger = getLogger('rest')


def get_font_scale(target_height_in_pixels: int):
    # Set a base scale
    scale = 1.0
    # Use a typical text
    text = "Test text"
    # Get the size of the text box
    ((text_width, text_height), _) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    # Calculate the target font scale
    target_font_scale = target_height_in_pixels / text_height
    return target_font_scale

def read_file_metadata(output_file):
    return {
        'n_files': 100,
        'image_pixel_width': 2016,
        'image_pixel_height': 2016,
        'dtype': 'uint16'
    }


def register_rest_interface(app, writer_manager: WriterRestManager, daq_manager: DaqRestManager,
                            sim_url_base: str, streamer, storage: StdDaqRedisStorage):

    script_dir = os.path.dirname(__file__)
    static_folder_path = os.path.join(script_dir, "static/")
    app.mount("/static", StaticFiles(directory=static_folder_path), name="static")

    @app.route('/')
    def react_app(_):
        return FileResponse('static/index.html')

    @app.route(FILE_METADATA)
    def get_file_metadata(acquisition_id: int):
        log = storage.get_log(log_id=acquisition_id)

        return {"status": "ok",
                "message": "Metadata retrieved.",
                'file_metadata': {
                    "log_info": log['info'],
                    "file_info": read_file_metadata(log['info']['output_file'])
                }}

    @app.get('/file/{acquisition_id}/{i_image}')
    def get_file_image(acquisition_id: int, i_image: int, module_map: Optional[int] = 0, gaps: Optional[int] = 0):
        _, daq_config = daq_manager.get_config()
        image_pixel_width = daq_config['image_pixel_width']
        image_pixel_height = daq_config['image_pixel_height']

        rectangle_color = (0, 255, 0)  # Green
        rectangle_thickness = 2  # Pixels
        text_color = (0, 255, 0)  # Green

        frame = np.random.randint(low=0, high=256, size=(image_pixel_height, image_pixel_width), dtype=np.uint8)

        image = cv2.resize(frame, (image_pixel_width, image_pixel_height))
        image = cv2.applyColorMap(image, cv2.COLORMAP_HOT)

        if module_map == 1:
            for key, (x_start, y_start, x_end, y_end) in daq_config['module_positions'].items():
                # Draw the rectangle
                cv2.rectangle(image, (x_start, y_start), (x_end, y_end), rectangle_color, rectangle_thickness)

                # Draw the text for the module and its submodules
                text_start_y = y_start if y_start < y_end else y_end
                size_y = abs(y_end - y_start) + 20
                gap_y = size_y // 5
                font_scale = get_font_scale(30)
                y_smaller = y_start if y_start < y_end else y_end
                y_bigger = y_end if y_end > y_start else y_start

                submodule_info = next((item for item in daq_config['submodule_info'] if item["submodule"] == int(key)), None)
                if submodule_info:
                    cv2.putText(image, f"module_id: {key}", (x_start + rectangle_thickness + 20,
                                                             text_start_y + (1*gap_y)),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, rectangle_thickness)
                    cv2.putText(image, f"hostname: {submodule_info['hostname']}",
                                (x_start + rectangle_thickness + 20, text_start_y + (2*gap_y)),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                                text_color, rectangle_thickness)
                    cv2.putText(image, f"port: {submodule_info['port']}",
                                (x_start + rectangle_thickness + 20, text_start_y + (3*gap_y)),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                                text_color, rectangle_thickness)
                    cv2.putText(image, f"row: {submodule_info['row']}, column: {submodule_info['column']}",
                        (x_start + rectangle_thickness + 20, text_start_y + (4 * gap_y)), cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale,
                        text_color, rectangle_thickness)

                arrow_color = (0, 255, 0)  # Red
                arrow_thickness = 20  # Pixels
                arrow_line_length = 100  # Length of the arrow's line
                arrow_tip_length = 30  # Length of the two lines that make the arrow tip

                arrow_start_x = x_end - 35  # adjust these as needed

                if y_start > y_end:  # if true, arrow points upwards
                    arrow_start_y = y_smaller + arrow_line_length + 20  # adjust these as needed
                    arrow_end_y = arrow_start_y - arrow_line_length
                    # Draw the arrow line
                    cv2.line(image, (arrow_start_x, arrow_start_y), (arrow_start_x, arrow_end_y), arrow_color,
                             arrow_thickness)
                    # Draw the arrow tip
                    cv2.line(image, (arrow_start_x, arrow_end_y),
                             (arrow_start_x - arrow_tip_length // 2, arrow_end_y + arrow_tip_length), arrow_color,
                             arrow_thickness)
                    cv2.line(image, (arrow_start_x, arrow_end_y),
                             (arrow_start_x + arrow_tip_length // 2, arrow_end_y + arrow_tip_length), arrow_color,
                             arrow_thickness)
                else:  # arrow points downwards
                    arrow_start_y = y_bigger - 120  # adjust these as needed
                    arrow_end_y = arrow_start_y + arrow_line_length
                    # Draw the arrow line
                    cv2.line(image, (arrow_start_x, arrow_start_y), (arrow_start_x, arrow_end_y), arrow_color,
                             arrow_thickness)
                    # Draw the arrow tip
                    cv2.line(image, (arrow_start_x, arrow_end_y),
                             (arrow_start_x - arrow_tip_length // 2, arrow_end_y - arrow_tip_length), arrow_color,
                             arrow_thickness)
                    cv2.line(image, (arrow_start_x, arrow_end_y),
                             (arrow_start_x + arrow_tip_length // 2, arrow_end_y - arrow_tip_length), arrow_color,
                             arrow_thickness)

        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 50])
        image_bytes = buffer.tobytes()

        img_io = BytesIO(image_bytes)

        return StreamingResponse(img_io, media_type='image/jpeg', headers={'Content-Length': str(len(image_bytes))})

    @app.post(WRITER_WRITE_SYNC_ENDPOINT, response_model=WriterResponse)
    def write_sync_request(write_request: WriteRequest):

        user_id = int(storage.get_config()[1]['writer_user_id'])

        validate_output_file(write_request.output_file, user_id)
        request_logger.info(f'Sync write {write_request.n_images} images with run_id '
                            f'{write_request.run_id} and file {write_request.output_file}')

        writer_status = writer_manager.write_sync(write_request.output_file,
                                                  write_request.n_images,
                                                  write_request.run_id)

        return {"status": "ok", "message": "Writing finished.", 'writer': writer_status}

    @app.post(WRITER_WRITE_ASYNC_ENDPOINT, response_model=WriterResponse)
    def write_async_request(write_request: WriteRequest):
        user_id = int(storage.get_config()[1]['writer_user_id'])
        validate_output_file(write_request.output_file, user_id)
        request_logger.info(f'Async write {write_request.n_images} images with run_id '
                            f'{write_request.run_id} and file {write_request.output_file}')

        writer_status = writer_manager.write_async(write_request.output_file,
                                                   write_request.n_images,
                                                   write_request.run_id)

        return {"status": "ok", "message": "Writing started.", 'writer': writer_status}

    @app.get(WRITER_STATUS_ENDPOINT, response_model=WriterResponse)
    def get_writer_status_request():
        writer_status = writer_manager.get_status()

        return {"status": "ok", "message": f"Writer is {writer_status['state']}",
                'writer': writer_status}

    @app.post(WRITER_STOP_ENDPOINT, response_model=WriterResponse)
    def stop_writing_request():
        request_logger.info(f'Stop write')
        writer_status = writer_manager.stop_writing()

        return {"status": "ok", "message": "Writing stopped.",
                'writer': writer_status}

    @app.get(SIM_STATUS_ENDPOINT, response_model=SimulatorResponse)
    def get_sim_status_request():
        try:
            status = requests.get(f'{sim_url_base}{STATUS_ENDPOINT}').json()
            return status
        except Exception as e:
            _logger.debug(f"Cannot communicate with simulator API on {sim_url_base}")
            return {'status': 'error', 'message': f'Cannot communicate with API on {sim_url_base}.'}

    @app.post(SIM_START_ENDPOINT, response_model=SimulatorResponse)
    def start_sim_request():
        request_logger.info(f'Start simulation')
        requests.post(f'{sim_url_base}{START_ENDPOINT}', data={}).json()
        return get_sim_status_request()

    @app.post(SIM_STOP_ENDPOINT, response_model=SimulatorResponse)
    def stop_sim_request():
        request_logger.info(f'Stop simulation')
        requests.post(f'{sim_url_base}{STOP_ENDPOINT}', data={}).json()
        return get_sim_status_request()

    @app.get(DAQ_LIVE_STREAM_ENDPOINT)
    def get_daq_live_stream_request():
        return StreamingResponse(streamer.generate_frames(), media_type='multipart/x-mixed-replace; boundary=frame')

    @app.get(DAQ_CONFIG_ENDPOINT)
    def get_daq_config_request():
        config_id, daq_config = daq_manager.get_config()

        if config_id is None:
            message = "No config set yet."
        else:
            message = f"DAQ configured for bit_depth={daq_config.get('bit_depth')}."

        return {"status": "ok", "message": message,
                'config': daq_config, 'config_id': config_id}

    @app.post(DAQ_CONFIG_ENDPOINT, response_model=ConfigResponse)
    def set_daq_config_request(config_change_request: ConfigRequest):
        request_logger.info(f'Setting new config {config_change_request}')

        daq_config = daq_manager.set_config(config_change_request)

        return {"status": "ok", "message": f"Setting new daq config.",
                'config': daq_config}

    @app.get(DAQ_STATS_ENDPOINT, response_model=StatsResponse)
    def get_daq_stats_request():
        stats = daq_manager.get_stats()
        return {"status": "ok", "message": f"DAQ statistics", 'stats': stats}

    @app.get(DAQ_LOGS_ENDPOINT, response_model=LogsResponse)
    def get_daq_logs_request(n_logs: int):
        logs = daq_manager.get_logs(n_logs)
        return {"status": "ok", "message": f"DAQ logs",
                'logs': logs}

    @app.get(DAQ_DEPLOYMENT_STATUS_ENDPOINT, response_model=DeploymentStatusResponse)
    def get_deployment_status_request():
        deployment_status = daq_manager.get_deployment_status()
        return {"status": "ok", "message": f"Deployment status",
                'deployment': deployment_status}

    @app.exception_handler(Exception)
    def error_handler(_, e):
        _logger.exception(e)
        return JSONResponse(status_code=200,
                            content={'status': 'error', 'message': str(e)})
