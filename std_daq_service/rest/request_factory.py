import datetime


def extract_write_request(request_data):

    if 'output_file' not in request_data:
        raise RuntimeError(f'Mandatory field missing: output_file')
    output_file = request_data['output_file']

    if 'n_images' not in request_data:
        raise RuntimeError(f'Mandatory field missing: n_images')
    n_images = request_data['n_images']

    if 'sources' not in request_data:
        raise RuntimeError('Mandatory field "sources" missing.')
    sources = request_data['sources']
    # if isinstance(request_data['sources'], list):
    #     raise RuntimeError('Field "sources" must be a list.')

    if 'user_id' not in request_data:
        raise RuntimeError('Mandatory field "user_id" missing.')
    user_id = request_data['user_id']

    return build_write_request(output_file=output_file, n_images=n_images, user_id=user_id)


# TODO: Add back sources to request.
def build_write_request(output_file, n_images, user_id):
    return {
        "output_file": output_file,
        'n_images': n_images,
        'user_id': user_id,
        'timestamp': datetime.datetime.now().timestamp()
    }


def build_user_response(response):
    return {
        'output_file': response['request_details']['output_file'],
        'status': response['status'],
        'init_timestamp': response['request_details']['timestamp'],
        'end_timestamp': datetime.datetime.now().timestamp()
    }


