from setuptools import setup

setup(
    name='std_daq_service',
    packages=['std_daq_service'],
    install_requires=[
        'std_buffer',
        'pyzmq',
        'pcaspy',
        'opencv-python',
        'tifffile',
        'protobuf',
        'flask',
        'flask-cors',
        'numpy',
        'redis'
    ],
    entry_points='''
        [console_scripts]
        epics_buffer=std_daq_service.epics_buffer.start:main
        epics_writer=std_daq_service.epics_writer.start:main
        epics_validator=std_daq_service.epics_validator.start:main
        std_daq_request=std_daq_service.tools.request:main
        std_daq_monitor=std_daq_service.tools.monitor:main
        std_daq_current_pulse_id=std_daq_service.tools.current_pulse_id:main
        
        std_daq_rest=std_daq_service.rest_v2.start:main
        std_daq_config_deployer=std_daq_service.tools.config_deployer:main
        std_daq_udp_simulator=std_daq_service.udp_simulator.start_rest:main
        
        std_cli_tune_network=std_daq_service.tools.tune_network:main
        std_cli_mjpeg_stream=std_daq_service.rest_v2.mjpeg:main
        std_cli_monitor_irq=std_daq_service.tools.monitor_irq:main
        std_cli_monitor_cpu=std_daq_service.tools.monitor_cpu:main
        std_cli_move_irq=std_daq_service.tools.move_irq:main
    ''',
)