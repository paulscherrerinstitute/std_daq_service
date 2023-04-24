import zmq
import numpy as np
import cv2

IPC_BASE = "ipc:///tmp"

def get_stream_addresses(detector_name):

    command_address = f'{IPC_BASE}/{detector_name}-writer'
    in_status_address = f'{IPC_BASE}/{detector_name}-writer-status-sync'
    out_status_address = f'{IPC_BASE}/{detector_name}-writer-status'
    image_metadata_address = f'{IPC_BASE}/{detector_name}-image'

    return command_address, in_status_address, out_status_address, image_metadata_address
