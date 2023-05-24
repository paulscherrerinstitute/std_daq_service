import argparse

from std_daq_client import StdDaqClient


def main():
    parser = argparse.ArgumentParser(description='Get std_daq config')
    parser.add_argument("--url_base", type=str, default='http://localhost:5000', help="Base URL of the REST Endpoint")
    args = parser.parse_args()

    client = StdDaqClient(url_base=args.url_base)
    print(client.get_config())


if __name__ == "__main__":
    main()
