import logging
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Event
from time import time, sleep


_logger = logging.getLogger(__name__)


def generate_udp_stream(generator, output_ip, start_udp_port, rep_rate=10, n_images=None,
                        stop_event=None, image_callback=lambda x: None):
    n_modules = generator.get_n_modules()
    n_packets = generator.get_n_packets()
    time_to_sleep = 1 / rep_rate

    udp_socket = socket(AF_INET, SOCK_DGRAM)

    if n_images is None:
        n_images = float('inf')

    if stop_event is None:
        stop_event = Event()

    i_image = 0
    iteration_start = time()
    while i_image < n_images and not stop_event.is_set():
        for i_packet in range(n_packets):
            for i_module in range(n_modules):
                udp_socket.sendto(generator.get_module_packet_bytes(i_module, i_packet, i_image),
                                  (output_ip, start_udp_port + i_module))

        _logger.debug(f'Send frames for {i_image}.')

        image_callback(i_image)

        iteration_end = time()
        time_left_to_sleep = max(0.0, time_to_sleep - (iteration_end - iteration_start))
        sleep(time_left_to_sleep)
        iteration_start = iteration_end
