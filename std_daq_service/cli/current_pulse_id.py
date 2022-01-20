import argparse
import os

from redis import Redis


def main():
    parser = argparse.ArgumentParser(description='Read current pulse_id.')
    parser.add_argument("--redis_host", type=str, help="Host of Redis instance.",
                        default=os.environ.get("REDIS_HOST", '127.0.0.1'))
    parser.add_argument("--channel", type=str, help="Channel with the pulse_id mapping", default="pulse_id")

    args = parser.parse_args()
    redis = Redis(host=args.redis_host)

    response = redis.xrevrange("pulse_id", max="+", count=1)
    received_pulse_id = int(response[0][0].decode().split('-')[0])

    print(received_pulse_id)


if __name__ == "__main__":
    main()
