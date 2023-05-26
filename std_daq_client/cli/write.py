import argparse
import json

from std_daq_client import StdDaqClient


def _process_arguments():
    parser = argparse.ArgumentParser(description='Get std_daq stats')
    parser.add_argument("--url_base", type=str, default='http://localhost:5000', help="Base URL of the REST Endpoint")
    parser.add_argument("output_file", type=str, help="Absolute path filename to write the data to.")
    parser.add_argument("n_images", type=int, help="Number of images to write.")
    args = parser.parse_args()

    write_request = {
        'output_file': args.output_file,
        'n_images': args.n_images
    }
    return args.url_base, write_request


def write_sync():
    url_base, write_request = _process_arguments()
    client = StdDaqClient(url_base)
    response = client.start_writer_sync(write_request)

    print(json.dumps(response, indent=2))


def write_async():
    url_base, write_request = _process_arguments()
    client = StdDaqClient(url_base)
    response = client.start_writer_async(write_request)

    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    # The default is sync, for no real reason.
    write_sync()
