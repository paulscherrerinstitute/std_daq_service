from time import sleep

import zmq
from std_buffer.std_daq.image_metadata_pb2 import ImageMetadata
from std_buffer.std_daq.writer_command_pb2 import WriterCommand, CommandType, RunInfo, WriterStatus

from std_daq_service.rest_v2.utils import set_ipc_rights
from std_daq_service.writer_driver.utils import get_stream_addresses

command_address, in_status_address, out_status_address, image_metadata_address = \
            get_stream_addresses('gf1')

ctx = zmq.Context()

run_info = {
  'output_file': "/sls/X02DA/Data10/e18600/disk4/output1.h5",
  'n_images': 100000
}

writer_command = WriterCommand()
writer_command.command_type = CommandType.START_WRITING
writer_command.run_info.CopyFrom(RunInfo(**run_info))
writer_command.metadata.Clear()

writer_command_sender = ctx.socket(zmq.PUB)
writer_command_sender.bind(command_address)
set_ipc_rights(command_address)

input('Press any key to start...')

image_metadata_receiver = ctx.socket(zmq.SUB)
image_metadata_receiver.connect(image_metadata_address)
image_metadata_receiver.subscribe(b"")

writer_command_sender.send(writer_command.SerializeToString())
sleep(0.1)

image_meta = ImageMetadata()
for i_image in range(10000):
    meta_raw = image_metadata_receiver.recv()
    image_meta.ParseFromString(meta_raw)

    writer_command.metadata.CopyFrom(image_meta)
    writer_command.command_type = CommandType.WRITE_IMAGE
    writer_command.i_image = i_image

    writer_command_sender.send(writer_command.SerializeToString())

writer_command.command_type = CommandType.STOP_WRITING
writer_command.metadata.Clear()
writer_command_sender.send(writer_command.SerializeToString())