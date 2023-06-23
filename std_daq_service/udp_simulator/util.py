from std_daq_service.udp_simulator.eiger import EGUdpPacketGenerator
from std_daq_service.udp_simulator.gigafrost import GFUdpPacketGenerator


def get_detector_generator(detector_type, image_height, image_width, bit_depth, n_modules, modules_info, image_filename=None):

    if detector_type == 'gigafrost':
        generator = GFUdpPacketGenerator(image_pixel_height=image_height,
                                         image_pixel_width=image_width,
                                         image_filename=image_filename)
        return generator
    elif detector_type == 'eiger':
        generator = EGUdpPacketGenerator(n_modules=n_modules,
                                         bit_depth=bit_depth,
                                         modules_info=modules_info)
        return generator
    else:
        raise ValueError(f"Detector type {detector_type} simulator not implemented.")