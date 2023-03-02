from pcaspy import SimpleServer

from std_daq_service.interface.start_stop.epics.driver import PV_NAME_APPLY_CONFIG, PV_NAME_START_WRITING, \
    PV_NAME_STOP_WRITING, PV_NAME_GET_STATUS, PV_NAME_GET_CONFIG, EpicsStartStopRestDriver


def start_ioc(detector_name, rest_url):
    prefix = f'STD-DAQ:{detector_name}:'

    pvdb = {
        # Command PVs
        PV_NAME_APPLY_CONFIG: {'type': 'int'},
        PV_NAME_START_WRITING: {'type': 'int'},
        PV_NAME_STOP_WRITING: {'type': 'int'},
        PV_NAME_GET_STATUS: {'type': 'int', 'scan': 1},
        PV_NAME_GET_CONFIG: {'type': 'int', 'scan': 1},

        # Writer state PVs
        'writer_state': {'type': 'string'},
        'writer_message': {'type': 'string'},

        # Acquisition PVs
        'acq_state': {'type': 'string'},
        'acq_n_images': {'type': 'int'},
        'acq_output_file': {'type': 'string'},
        'acq_n_writes_complete': {'type': 'int'},
        'acq_n_writes_requested': {'type': 'int'},
        'acq_start_time': {'type': 'float'},
        'acq_stop_time': {'type': 'float'},

        # Write request PVs.
        'n_images': {'type': 'int'},
        'output_file': {'type': 'string'},

        # Configuration PVs.
        'bit_depth': {'type': 'enum', 'enums': ['4', '8', '16', '32']},
        'detector_name': {'type': 'string'},
        'detector_type': {'type': 'string'},
        'image_pixel_height': {'type': 'int'},
        'image_pixel_width': {'type': 'int'},
        'n_modules': {'type': 'int'},
        'start_udp_port': {'type': 'int'},
    }

    server = SimpleServer()
    server.createPV(prefix, pvdb)
    driver = EpicsStartStopRestDriver(rest_url=rest_url)

    # process CA transactions
    while True:
        server.process(0.1)


if __name__ == '__main__':
    detector_name = 'eiger'
    rest_url = 'http://127.0.0.1:5000'
    start_ioc(detector_name=detector_name, rest_url=rest_url)
