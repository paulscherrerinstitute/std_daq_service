import argparse
import json
import os

from std_daq_client import StdDaqClient


def get_config():
    parser = argparse.ArgumentParser(description='Get std_daq config')
    parser.add_argument("-b", type=str, default=os.environ.get('STD_DAQ_API_URL', 'http://127.0.0.1:5000'),
                        help="Base URL of the REST Endpoint. Read also from environment variable STD_DAQ_API_URL")
    args = parser.parse_args()

    client = StdDaqClient(url_base=args.b)
    print(json.dumps(client.get_config(), indent=2))


def set_config():
    parser = argparse.ArgumentParser(description='Set std_daq config')
    parser.add_argument("config_file", type=str, help="File to load the config from.")
    parser.add_argument("-b", type=str, default=os.environ.get('STD_DAQ_API_URL', 'http://127.0.0.1:5000'),
                        help="Base URL of the REST Endpoint. Read also from environment variable STD_DAQ_API_URL")
    args = parser.parse_args()

    with open(args.config_file) as input_file:
        daq_config = json.load(input_file)

    client = StdDaqClient(url_base=args.b)
    print(json.dumps(client.set_config(daq_config=daq_config), indent=2))


def get_deploy_status():
    parser = argparse.ArgumentParser(description='Get std_daq deployment status')
    parser.add_argument("-b", type=str, default=os.environ.get('STD_DAQ_API_URL', 'http://127.0.0.1:5000'),
                        help="Base URL of the REST Endpoint. Read also from environment variable STD_DAQ_API_URL")
    args = parser.parse_args()

    client = StdDaqClient(url_base=args.b)
    print(json.dumps(client.get_deployment_status(), indent=2))


def get_logs():
    parser = argparse.ArgumentParser(description='Get std_daq logs')
    parser.add_argument("-n", type=int, default=1, help="Number of last logs to return")
    parser.add_argument("-b", type=str, default=os.environ.get('STD_DAQ_API_URL', 'http://127.0.0.1:5000'),
                        help="Base URL of the REST Endpoint. Read also from environment variable STD_DAQ_API_URL")
    args = parser.parse_args()

    client = StdDaqClient(url_base=args.b)
    print(json.dumps(client.get_logs(args.n), indent=2))


def get_stats():
    parser = argparse.ArgumentParser(description='Get std_daq stats')
    parser.add_argument("-b", type=str, default=os.environ.get('STD_DAQ_API_URL', 'http://127.0.0.1:5000'),
                        help="Base URL of the REST Endpoint. Read also from environment variable STD_DAQ_API_URL")
    args = parser.parse_args()

    client = StdDaqClient(url_base=args.url_base)
    print(json.dumps(client.get_stats(), indent=2))


def get_status():
    parser = argparse.ArgumentParser(description='Get std_daq status')
    parser.add_argument("-b", type=str, default=os.environ.get('STD_DAQ_API_URL', 'http://127.0.0.1:5000'),
                        help="Base URL of the REST Endpoint. Read also from environment variable STD_DAQ_API_URL")
    args = parser.parse_args()

    client = StdDaqClient(url_base=args.url_base)
    print(json.dumps(client.get_status(), indent=2))


def write_sync():
    parser = argparse.ArgumentParser(description='Start std_daq sync write')
    parser.add_argument("-b", type=str, default=os.environ.get('STD_DAQ_API_URL', 'http://127.0.0.1:5000'),
                        help="Base URL of the REST Endpoint. Read also from environment variable STD_DAQ_API_URL")
    parser.add_argument("output_file", type=str, help="Absolute path filename to write the data to.")
    parser.add_argument("n_images", type=int, help="Number of images to write.")
    args = parser.parse_args()

    client = StdDaqClient(url_base=args.b)
    response = client.start_writer_sync({'output_file': args.output_file, 'n_images': args.n_images})

    print(json.dumps(response, indent=2))


def write_async():
    parser = argparse.ArgumentParser(description='Start std_daq async write')
    parser.add_argument("-b", type=str, default=os.environ.get('STD_DAQ_API_URL', 'http://127.0.0.1:5000'),
                        help="Base URL of the REST Endpoint. Read also from environment variable STD_DAQ_API_URL")
    parser.add_argument("output_file", type=str, help="Absolute path filename to write the data to.")
    parser.add_argument("n_images", type=int, help="Number of images to write.")
    args = parser.parse_args()

    client = StdDaqClient(url_base=args.b)
    response = client.start_writer_async({'output_file': args.output_file, 'n_images': args.n_images})

    print(json.dumps(response, indent=2))


def write_stop():
    parser = argparse.ArgumentParser(description='std_daq stop writer')
    parser.add_argument("--url_base", type=str, default='http://localhost:5000', help="Base URL of the REST Endpoint")
    url_base = parser.parse_args().url_base

    client = StdDaqClient(url_base)
    response = client.stop_writer()

    print(json.dumps(response, indent=2))
