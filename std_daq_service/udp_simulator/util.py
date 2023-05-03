from std_daq_service.udp_simulator.gigafrost import GFUdpPacketGenerator


def get_detector_generator(detector_type, image_height, image_width, image_filename=None):

    if detector_type == 'gigafrost':
        generator = GFUdpPacketGenerator(image_pixel_height=image_height,
                                         image_pixel_width=image_width,
                                         image_filename=image_filename)
        return generator
    else:
        raise ValueError(f"Detector type {detector_type} simulator not implemented.")