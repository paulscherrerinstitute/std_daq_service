
def get_stream_addresses(detector_name):

    image_metadata_stream = f'{detector_name}-image'
    writer_control_stream = f'{detector_name}-writer'
    writer_status_stream = f'{detector_name}-writer-status'

    return image_metadata_stream, writer_control_stream, writer_status_stream
