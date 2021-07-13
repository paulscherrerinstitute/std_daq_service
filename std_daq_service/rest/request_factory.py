from datetime import datetime


def build_write_request(output_file, n_images, sources, run_id):
    header = None
    return (header, { "output_file": output_file,
        "n_images":n_images,
        "run_id": run_id,
        "sources": sources,
        "timestamp": datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
    })


def build_broker_response(response):
    # TODO: Convert the response into something the user can read.
    return response


def build_kill_request(request_id):
    # TODO: Decide on how to format of the kill request.
    return None
