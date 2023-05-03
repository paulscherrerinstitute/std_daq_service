import copy
from collections import deque
from threading import Thread, Event, Lock, Semaphore
from google.protobuf.json_format import MessageToDict
from std_buffer.std_daq.image_metadata_pb2 import ImageMetadata
from std_buffer.std_daq.writer_command_pb2 import WriterCommand, CommandType, RunInfo, WriterStatus
from time import time, sleep, time_ns
import logging
import zmq

_logger = logging.getLogger(__name__)

STATS_INTERVAL_TIME = 0.5
WRITER_STATUS_TIMEOUT_MS = 500
# In seconds.
RECV_TIMEOUT_MS = 200
SYNC_WINDOW_SIZE = 2
N_LOGS = 50

WRITER_STATUS_POLL_INTERVAL = 0.1
WRITER_STATUS_POLL_N_ATTEMPTS = 50


class WriterStatusTracker(object):
    EMPTY_STATS = {"n_write_completed": 0, "n_write_requested": 0, "start_time": None, "stop_time": None}

    def __init__(self, ctx, in_status_address, out_status_address, n_max_active_requests):
        self.ctx = ctx
        self.n_max_active_requests = n_max_active_requests
        self.stop_event = Event()
        self.rate_limiter = None

        self.status = {'state': 'READY', 'acquisition': {'state': "FINISHED",
                                                         'info': {'n_images': 0},
                                                         'stats': dict(self.EMPTY_STATS)}}
        self.status_lock = Lock()

        self.last_status_send_time = 0
        self._current_run_id = None

        self.status_receiver = self.ctx.socket(zmq.PULL)
        self.status_receiver.RCVTIMEO = WRITER_STATUS_TIMEOUT_MS
        self.status_receiver.bind(in_status_address)

        self.status_sender = self.ctx.socket(zmq.PUB)
        self.status_sender.bind(out_status_address)

        self._status_thread = Thread(target=self._status_rcv_thread)
        self._status_thread.start()

    def get_status(self):
        with self.status_lock:
            return self.status

    def _status_rcv_thread(self):
        status_message = WriterStatus()

        while not self.stop_event.is_set():
            try:
                status = self.status_receiver.recv()
                status_message.ParseFromString(status)

                status_run_id = status_message.run_info.run_id

                if status_message.command_type == CommandType.START_WRITING:
                    self._log_start_status(status_run_id, status_message)
                    continue

                if status_message.command_type == CommandType.STOP_WRITING:
                    self._log_stop_status(status_message)
                    continue

                if status_run_id != self._current_run_id:
                    _logger.warning(f"Received write status for run_id={status_run_id} while the "
                                    "_current_run_id={self._current_run_id}. Status={status_message}")
                    self.status['state'] = 'WRITING'
                    continue

                if status_message.command_type == CommandType.WRITE_IMAGE:
                    self._log_write_status(status_message)
                    continue

                _logger.warning(f"Unknown status message received: {status_message}")
            except zmq.Again:
                pass

    def _log_write_status(self, status):
        with self.status_lock:
            self.status['state'] = 'WRITING'
            self.status['acquisition']['state'] = 'ACQUIRING_IMAGES'
            self.status['acquisition']['stats']['n_write_completed'] += 1

        self.rate_limiter.release()

        # Send out write progress updates on STATS_INTERVAL_TIME intervals.
        current_time = time()
        if current_time - self.last_status_send_time > STATS_INTERVAL_TIME:
            self.last_status_send_time = current_time
            self.status_sender.send_json(self.status)

    def _log_start_status(self, run_id, status):
        with self.status_lock:
            self.status = {'state': "WRITING",
                           'acquisition': {'state': 'WAITING_IMAGES',
                                           'stats': dict(self.EMPTY_STATS),
                                           'info': {'output_file': status.run_info.output_file,
                                                    'n_images': status.run_info.n_images,
                                                    'run_id': run_id}}}
            self.status['acquisition']['stats']['start_time'] = time()

        self.last_status_send_time = 0
        self._current_run_id = run_id
        self.rate_limiter = Semaphore(self.n_max_active_requests)

        # Send status update as soon as writer starts.
        self.status_sender.send_json(self.status)

    def _log_stop_status(self, status):
        with self.status_lock:
            self.status['state'] = 'READY'
            self.status['acquisition']['state'] = 'FINISHED'
            self.status['acquisition']['stats']['stop_time'] = time()

        self._current_run_id = None

        # Send status update as soon as writer stops.
        self.status_sender.send_json(self.status)

    def log_write_request(self, run_id, image_id):
        if run_id != self._current_run_id:
            _logger.warning(
                f"Received write_request for image_id={image_id}, run_id={run_id} while the _current_run_id={self._current_run_id}.")
            return

        self.rate_limiter.acquire()

        with self.status_lock:
            self.status['acquisition']['stats']['n_write_requested'] += 1

    def close(self):
        _logger.info("Closing writer status.")

        self.stop_event.set()
        self._status_thread.join()


class WriterDriver(object):
    WRITER_DRIVER_IPC_ADDRESS = 'inproc://WriterDriverCommand'
    POLLER_TIMEOUT_MS = 1000
    # In seconds.
    STARTUP_WAIT_TIME = 200 / 1000

    START_COMMAND = 'START'
    STOP_COMMAND = 'STOP'

    def __init__(self, ctx, command_address, in_status_address, out_status_address, image_metadata_address):
        _logger.info(f'Starting writer driver with:\n' \
                     f'\t command_address:{command_address}\n' \
                     f'\t in_status_address:{in_status_address}\n' \
                     f'\t out_status_address:{out_status_address}\n' \
                     f'\t image_metadata_address:{image_metadata_address}')
        self.out_status_address = out_status_address

        self.ctx = ctx
        self.stop_event = Event()
        self.status = WriterStatusTracker(ctx, in_status_address, out_status_address, SYNC_WINDOW_SIZE)

        # Inter-thread communication (send commands from user to communication thread)
        self.user_command_sender = self.ctx.socket(zmq.PUSH)
        self.user_command_sender.bind(self.WRITER_DRIVER_IPC_ADDRESS)

        # Inter-thread communication (recv commands from user in communication thread)
        self.user_command_receiver = self.ctx.socket(zmq.PULL)
        self.user_command_receiver.connect(self.WRITER_DRIVER_IPC_ADDRESS)

        # Send commands to writer instances.
        self.writer_command_sender = self.ctx.socket(zmq.PUB)
        self.writer_command_sender.bind(command_address)

        # Receive the image metadata stream from the detector.
        self.image_metadata_receiver = self.ctx.socket(zmq.SUB)
        self.image_metadata_receiver.connect(image_metadata_address)

        self.image_meta = ImageMetadata()
        self.writer_command = WriterCommand()

        self.communication_t = Thread(target=self._communication_thread)
        self.communication_t.start()

    def get_status(self):
        return self.status.get_status()

    def start(self, run_info):
        _logger.info(f"Start acquisition requested.")

        status = self.get_status()
        if status['state'] != "READY":
            raise RuntimeError(f"Cannot start new acquisition while previous one is running:\n {status}")

        self.user_command_sender.send_json({'COMMAND': self.START_COMMAND, 'run_info': run_info or {}})

        self.wait_for_state("WRITING")

    def stop(self):
        _logger.info(f"Stop acquisition requested.")
        self.user_command_sender.send_json({'COMMAND': self.STOP_COMMAND})

        self.wait_for_state('READY')

    def close(self):
        _logger.info(f'Closing writer driver.')
        self.status.close()

        self.stop_event.set()
        self.communication_t.join()

    def _communication_thread(self):
        # Wait for connections to happen.
        sleep(self.STARTUP_WAIT_TIME)

        poller = zmq.Poller()
        poller.register(self.user_command_receiver, zmq.POLLIN)
        poller.register(self.image_metadata_receiver, zmq.POLLIN)

        i_image = 0
        while not self.stop_event.is_set():
            try:
                events = dict(poller.poll(timeout=RECV_TIMEOUT_MS))

                if self.user_command_receiver in events:
                    command = self.user_command_receiver.recv_json(flags=zmq.NOBLOCK)

                    if command['COMMAND'] == self.START_COMMAND:
                        run_info = command['run_info']

                        self._execute_start_command(run_info)
                        i_image = 0

                    elif command['COMMAND'] == self.STOP_COMMAND:
                        self._execute_stop_command()

                    else:
                        _logger.warning(f"Unknown command:{command}.")

                if self.image_metadata_receiver in events:
                    meta_raw = self.image_metadata_receiver.recv(flags=zmq.NOBLOCK)
                    self.image_meta.ParseFromString(meta_raw)

                    self._execute_write_command(i_image)
                    i_image += 1

                    # Terminate writing.
                    if i_image == self.writer_command.run_info.n_images:
                        self._execute_stop_command()

            except Exception as e:
                _logger.exception("Error in driver loop.")

    def _execute_start_command(self, run_info):
        # Tell the writer to start writing.
        self.writer_command.command_type = CommandType.START_WRITING
        self.writer_command.run_info.CopyFrom(RunInfo(**run_info))
        self.writer_command.metadata.Clear()

        _logger.debug(f"Send start command to writer: {self.writer_command}.")
        self.writer_command_sender.send(self.writer_command.SerializeToString())

        self.wait_for_state('WRITING')

        # Subscribe to the ImageMetadata stream.
        self.image_metadata_receiver.setsockopt(zmq.SUBSCRIBE, b'')

    def _execute_stop_command(self):
        # Stop listening to new image metadata.
        self.image_metadata_receiver.setsockopt(zmq.UNSUBSCRIBE, b'')

        # Drain image_metadata received so far.
        try:
            self.image_metadata_receiver.recv(flags=zmq.NOBLOCK)
        except zmq.Again:
            pass

        self.writer_command.command_type = CommandType.STOP_WRITING
        self.writer_command.metadata.Clear()

        _logger.debug(f"Send stop command to writer: {self.writer_command}.")
        self.writer_command_sender.send(self.writer_command.SerializeToString())

        self.wait_for_state('READY')

    def _execute_write_command(self, i_image):

        self.writer_command.metadata.CopyFrom(self.image_meta)
        self.writer_command.command_type = CommandType.WRITE_IMAGE
        self.writer_command.i_image = i_image

        self.status.log_write_request(self.writer_command.run_info.run_id, self.image_meta.image_id)
        self.writer_command_sender.send(self.writer_command.SerializeToString())

    def wait_for_state(self, target_state, poll_interval=WRITER_STATUS_POLL_INTERVAL):
        for _ in range(WRITER_STATUS_POLL_N_ATTEMPTS):
            sleep(poll_interval)
            status = self.get_status()
            if status['state'] == target_state:
                return
        else:
            raise RuntimeError(f"Cannot reach {target_state} state. The writer needs to be restarted.")
