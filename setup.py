from setuptools import setup

setup(
    name='std_daq_service',
    version='1.0',
    py_modules=['std_daq_service'],
    install_requires=[
        'pyzmq',
        'pyepics',
        'flask',
        'pika',
        'redis',
        'pcaspy'
    ],
    entry_points='''
        [console_scripts]
        epics_buffer=std_daq_service.epics_buffer.start:main
    ''',
)