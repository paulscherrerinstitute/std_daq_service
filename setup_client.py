import os

from setuptools import setup

CLIENT_VERSION = "1.3.2"

with open(os.path.join(os.path.dirname(__file__), 'std_daq_client/', 'README.md')) as readme:
    long_description = readme.read()

setup(
    version=CLIENT_VERSION,
    name='std_daq_client',
    packages=['std_daq_client'],
    install_requires=[
        'requests',
    ],
    entry_points='''
        [console_scripts]
        std_cli_get_config=std_daq_client.cli:get_config
        std_cli_get_deploy_status=std_daq_client.cli:get_deploy_status
        std_cli_get_logs=std_daq_client.cli:get_logs
        std_cli_get_stats=std_daq_client.cli:get_stats
        std_cli_get_status=std_daq_client.cli:get_status
        std_cli_write_async=std_daq_client.cli:write_sync
        std_cli_write_sync=std_daq_client.cli:write_async
        std_cli_write_stop=std_daq_client.cli:write_stop
    ''',

    author="Paul Scherrer Institute",
    url='https://github.com/paulscherrerinstitute/std_daq_service',
    description='Python client for standard-daq',
    long_description=long_description,
    long_description_content_type='text/markdown',
)
