import datetime


def build_write_request(output_file, n_images, sources):
    return {
        "output_file": output_file,
        'n_images': n_images,
        'timestamp': datetime.datetime.now().timestamp()
    }


def build_broker_response(response):
    # TODO: Convert the response into something the user can read.
    return response
