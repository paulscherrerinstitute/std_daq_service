import json
from collections import OrderedDict

DAQ_CONFIG_FIELDS = ['detector_name', 'detector_type',
                     'bit_depth', 'image_pixel_height', 'image_pixel_width', 'n_modules', 'start_udp_port',
                     'writer_user_id', 'module_positions', 'submodule_info']

DAQ_CONFIG_INT_FIELDS = ['bit_depth', 'image_pixel_height', 'image_pixel_width', 'n_modules', 'start_udp_port',
                         'writer_user_id']

IPC_BASE = "ipc:///tmp"


def load_daq_config(config_file):
    with open(config_file, 'r') as input_file:
        daq_config = json.load(input_file)
    validate_config(daq_config)

    return daq_config


def validate_config(new_config):
    error_message = ""
    for field_name in DAQ_CONFIG_FIELDS:
        if field_name not in new_config:
            error_message += f' missing {field_name},'
        elif field_name in DAQ_CONFIG_INT_FIELDS:
            try:
                new_config[field_name] = int(new_config[field_name])
            except ValueError:
                error_message += f' non-int value {field_name};'

    if error_message:
        raise RuntimeError(f"Config errors:{error_message}")


def get_stream_addresses(detector_name):

    command_address = f'{IPC_BASE}/{detector_name}-writer'
    in_status_address = f'{IPC_BASE}/{detector_name}-writer-status-sync'
    out_status_address = f'{IPC_BASE}/{detector_name}-writer-status'
    image_metadata_address = f'{IPC_BASE}/{detector_name}-image'

    return command_address, in_status_address, out_status_address, image_metadata_address


def update_config(old_config, config_updates):
    if old_config is not None:
        new_config = OrderedDict({param: getattr(config_updates, param, old_config[param])
                                  for param in DAQ_CONFIG_FIELDS})
    else:
        new_config = config_updates

    validate_config(new_config)

    return new_config
