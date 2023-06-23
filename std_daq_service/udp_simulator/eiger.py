import logging

import numpy as np
from std_buffer.eiger.data import (EG_MAX_PAYLOAD, MODULE_X_SIZE,
                                   MODULE_Y_SIZE, EgUdpPacket,
                                   calculate_udp_packet_info)

_logger = logging.getLogger("EGUdpPacketGenerator")

class EGUdpPacketGenerator(object):
    def __init__(self, n_modules, bit_depth, modules_info):
        # sizes of a module are fixed
        self.image_pixel_height = MODULE_Y_SIZE
        self.image_pixel_width = MODULE_X_SIZE
        self.bit_depth = bit_depth
        self.n_modules = n_modules
        self.modules_info = modules_info

        _logger.info(f"Initializing Eiger udp simulator for {n_modules} modules with width {self.image_pixel_height} height {self.image_pixel_width} each and bit depth {self.bit_depth}.")
        
        udp_packet_info = calculate_udp_packet_info(self.image_pixel_height, self.image_pixel_width, self.bit_depth, self.n_modules)
        self.frame_n_packets = udp_packet_info['frame_n_packets']
        self.packet_n_rows = udp_packet_info['packet_n_rows']
        self.last_packet_n_rows = udp_packet_info['last_packet_n_rows']
        self.packet_n_data_bytes = udp_packet_info['packet_n_data_bytes']
        self.last_packet_n_data_bytes = udp_packet_info['last_packet_n_data_bytes']
        
        self.module_packets = self._generate_module_packets()

    def _generate_module_packets(self):
        module_packets = []

        for i_module in range(self.n_modules):
            packets = self._generate_packets(i_module, self.bit_depth, self.modules_info[i_module]['row'], self.modules_info[i_module]['column'])
            module_packets.append(packets)

        return module_packets

    def _generate_packets(self, i_module, bit_depth, row, column):
        packets = []
        bit_depth = 32
        for i_packet in range(self.frame_n_packets):

            packet_header = self._generate_packet_header(i_module, i_packet, row, column)
            if bit_depth == 8:
                dtype_bit_depth = np.uint8 
                element_size = np.dtype(np.uint8).itemsize
            elif bit_depth == 16:
                dtype_bit_depth = np.uint16
                element_size = np.dtype(np.uint16).itemsize
            elif bit_depth == 32:
                dtype_bit_depth = np.uint32
                element_size = np.dtype(np.uint32).itemsize
            else:
                raise ValueError(f"Bit depth {bit_depth} not supported.")
        
            if EG_MAX_PAYLOAD % element_size != 0:
                buffer_size = (EG_MAX_PAYLOAD // element_size + 1) * element_size
            else:
                buffer_size = EG_MAX_PAYLOAD

            # creates the array with the help of the buffer
            packet_image_bytes = np.ndarray(shape=(buffer_size // element_size,), dtype=dtype_bit_depth, buffer=bytearray(buffer_size)).newbyteorder('L')
            # fills the array with the module number
            packet_image_bytes.fill(i_module)

            packets.append((packet_header, packet_image_bytes.tobytes()))

        return packets
    
    def _generate_packet_header(self, i_module, i_packet, row, column):
        udp_packet = EgUdpPacket(
            frame_num = 0,
            exp_length = 0,
            packet_number = i_packet,
            detSpec1 = 0,
            timestamp = 0,
            module_id = i_module,
            row = row,
            column = column,
            detSpec2 = 0,
            detSpec3 = 0,
            round_robin = 0,
            detector_type = 1,
            header_version = 2
        )
        return udp_packet
    
    def get_module_packet_bytes(self, i_module, i_packet, i_image):
        packet_header, packet_image_bytes = self.module_packets[i_module][i_packet]
        packet_header.frame_num = i_image
        return bytes(packet_header) + packet_image_bytes

    def get_n_modules(self):
        return len(self.module_packets)

    def get_n_packets(self):
        return len(self.module_packets[0])