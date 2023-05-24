from setuptools import setup

CLIENT_VERSION = "1.0.0"

setup(
    version=CLIENT_VERSION,
    name='std_daq_client',
    packages=['std_daq_client'],
    install_requires=[
        'requests',
    ],
    entry_points='''
        [console_scripts]
        std_cli_get_config=std_daq_client.cli.get_config:main
        std_cli_get_deploy_status=std_daq_client.cli.get_deploy_status:main
        std_cli_get_logs=std_daq_client.cli.get_logs:main
        std_cli_get_stats=std_daq_client.cli.get_stats:main
        std_cli_get_status=std_daq_client.cli.get_status:main
    ''',
)