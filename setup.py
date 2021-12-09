from setuptools import setup

setup(
    name='std_daq_service',
    entry_points='''
        [console_scripts]
        epics_buffer=std_daq_service.epics_buffer.start:main
    ''',
)