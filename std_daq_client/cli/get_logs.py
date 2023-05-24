import argparse
import json

from std_daq_client import StdDaqClient


def main():
    parser = argparse.ArgumentParser(description='Get std_daq logs')
    parser.add_argument("--url_base", type=str, default='http://localhost:5000', help="Base URL of the REST Endpoint")
    parser.add_argument("--n_logs", type=int, default=5, help="Number of last logs to return")
    args = parser.parse_args()

    client = StdDaqClient(url_base=args.url_base)
    print(json.dumps(client.get_logs(args.n_logs), indent=2))


if __name__ == "__main__":
    main()
