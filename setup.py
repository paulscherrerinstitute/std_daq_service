from setuptools import setup

setup(
    name='std_daq_service',
    entry_points='''
        [console_scripts]
        epics_buffer=std_daq_service.epics_buffer.start:main
        epics_writer=std_daq_service.epics_writer.start:main
        epics_validator=std_daq_service.epics_validator.start:main
        std_daq_request=std_daq_service.cli.request:main
        std_daq_monitor=std_daq_service.cli.monitor:main
        std_daq_current_pulse_id=std_daq_service.cli.current_pulse_id:main
    ''',
)