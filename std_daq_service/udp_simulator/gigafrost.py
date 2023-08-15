import tifffile
import numpy as np
import logging

from std_buffer.gigafrost.data import calculate_udp_packet_info, GfUdpPacket
from std_buffer.gigafrost.udp_sim_gf import GF_N_MODULES

_logger = logging.getLogger("GFUdpPacketGenerator")


class GFUdpPacketGenerator(object):
    def __init__(self, image_pixel_height, image_pixel_width, image_filename=None):
        self.image_pixel_height = image_pixel_height
        self.image_pixel_width = image_pixel_width
        self.image_filename = image_filename

        self.quadrant_height = image_pixel_height // 2
        self.quadrant_width = image_pixel_width // 2

        _logger.info(f"Initializing Gigafrost udp simulator with width {image_pixel_width} height {image_pixel_height}.")

        if image_filename:
            self.image = tifffile.imread(image_filename)
        else:
            self.image = self._generate_default_image()

        if (image_pixel_height, image_pixel_width) != self.image.shape:
            raise RuntimeError(f"Wrong dimensions of provided image. "
                               f"Expected size [{image_pixel_height}, {image_pixel_width}], "
                               f"but got {self.image.shape}")

        # Scale image to 12 bits - (2 ** 12 - 1)
        self.image = np.multiply(self.image, (2 ** 12 - 1) / self.image.max(), casting='unsafe').astype('uint16')

        udp_packet_info = calculate_udp_packet_info(image_pixel_height, image_pixel_width)
        self.frame_n_packets = udp_packet_info['frame_n_packets']
        self.packet_n_rows = udp_packet_info['packet_n_rows']
        self.last_packet_n_rows = udp_packet_info['last_packet_n_rows']
        self.packet_n_data_bytes = udp_packet_info['packet_n_data_bytes']
        self.last_packet_n_data_bytes = udp_packet_info['last_packet_n_data_bytes']

        # self.quadrant_id, self.link_id, self.swap = self._calculate_quadrant_info(i_module)
        self.module_packets = self._generate_module_packets()

    def _generate_default_image(self):
        return np.random.randint(10000, 50000, (self.image_pixel_height, self.image_pixel_width), dtype=np.uint16)

    def _calculate_quadrant_info(self, i_module):
        quadrant_id = i_module // 2
        link_id = i_module % 2
        swap = 1 if quadrant_id % 2 == 0 else 0

        return quadrant_id, link_id, swap

    def _generate_module_packets(self):
        module_packets = []

        for i_module in range(GF_N_MODULES):
            quadrant_id, link_id, swap = self._calculate_quadrant_info(i_module)
            module_image = self._get_module_image(quadrant_id, link_id)
            packets = self._generate_packets(i_module, module_image)

            module_packets.append(packets)

        return module_packets

    def _get_module_image(self, quadrant_id, link_id):
        # Crop the needed quadrant from the image
        if quadrant_id == 0:
            quadrant_data = self.image[:self.quadrant_height, :self.quadrant_width]  # NW
        elif quadrant_id == 1:
            quadrant_data = self.image[:self.quadrant_height, self.quadrant_width:]  # NE
        elif quadrant_id == 2:
            quadrant_data = self.image[self.quadrant_height:, :self.quadrant_width]  # SW
        elif quadrant_id == 3:
            quadrant_data = self.image[self.quadrant_height:, self.quadrant_width:]  # SE
        else:
            raise ValueError(f"Unknown quadrant_id={quadrant_id}.")

        # Get even (link_id == 0) or odd (link_id == 1) lines of the quadrant.
        module_data = quadrant_data[link_id::2]

        # Top modules are streamed in reverse(NW, NE)
        if quadrant_id < 2:
            module_data = module_data[::-1]

        return module_data

    def _generate_packets(self, i_module, module_image):
        packets = []

        # First n-1 packets are the same.
        for i_packet in range(self.frame_n_packets):

            packet_n_rows = self.packet_n_rows
            packet_n_data_bytes = self.packet_n_data_bytes

            # Last packet.
            if i_packet == self.frame_n_packets - 1:
                packet_n_data_bytes = self.last_packet_n_data_bytes

            packet_header = self._generate_packet_header(i_module, i_packet)
            packet_image_bytes = self._generate_packet_image_bytes(
                i_packet, packet_n_rows, packet_n_data_bytes, module_image)

            packets.append((packet_header, packet_image_bytes))

        return packets

    def _generate_packet_image_bytes(self, i_packet, n_rows_per_packet, n_bytes_per_packet, module_image):
        packet_starting_row = n_rows_per_packet * i_packet

        packet_image_bytes = 0
        i_pixel = 0
        for i_row in range(n_rows_per_packet):
            i_module_row = i_row + packet_starting_row

            for i_module_col in range(self.quadrant_width):
                pixel_value = int(module_image[i_module_row, i_module_col])
                packet_image_bytes |= pixel_value << (i_pixel * 12)
                i_pixel += 1

        return packet_image_bytes.to_bytes(n_bytes_per_packet, 'little')

    def _generate_packet_header(self, i_module, i_packet):
        quadrant_id, link_id, swap = self._calculate_quadrant_info(i_module)

        udp_packet = GfUdpPacket()

        # To be changed at runtime.
        udp_packet.frame_index = 0
        udp_packet.scan_id = 0

        # Fixed properties
        udp_packet.protocol_id = 203
        udp_packet.scan_time = 100000
        udp_packet.sync_time = 200000
        udp_packet.image_timing = 300000
        udp_packet.image_status_flags = 0
        udp_packet.quadrant_row_length_in_blocks = self.image_pixel_width // 2 // 12

        quadrant_height = self.image_pixel_height // 2
        # The last bit in the 'quadrant_row' is the 'swap' bit.
        udp_packet.quadrant_rows = (quadrant_height & 0xFF) + swap

        # Octant dependent properties
        udp_packet.status_flags = 0
        udp_packet.status_flags |= (quadrant_id << 6)
        udp_packet.status_flags |= (link_id << 5)
        udp_packet.status_flags |= quadrant_height >> 8
        # No idea what this means - its just what we dumped when recording the detector.
        corr_mode = 5
        udp_packet.status_flags |= (corr_mode << 2)

        # Packet dependent properties
        udp_packet.packet_starting_row = self.packet_n_rows * i_packet

        return udp_packet

    def get_module_packet_bytes(self, i_module, i_packet, image_id, scan_id=0):
        packet_header, packet_bytes = self.module_packets[i_module][i_packet]

        # Adjust for current frame
        packet_header.frame_index = image_id
        packet_header.scan_id = scan_id

        return bytes(packet_header) + packet_bytes

    def get_n_modules(self):
        return len(self.module_packets)

    def get_n_packets(self):
        return len(self.module_packets[0])


