import asyncio
from threading import Thread
from time import time

from grpc.aio import Channel

from std_daq_service.writer_driver.start_stop import start_stop_writer_pb2_grpc, start_stop_writer_pb2


class Client(object):
    def __init__(self, address='localhost:50051'):
        self.status = {}
        self.command = None

        self.loop = asyncio.new_event_loop()
        self._async_t = Thread(target=self._run_event_loop(self.loop), args=(self.loop,))
        self._async_t.start()

        future = asyncio.run_coroutine_threadsafe(self._run_gprc(address), self.loop)
        future.result()
        asyncio.run_coroutine_threadsafe(self._recv_status(), self.loop)

    def _run_event_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def _run_gprc(self, address):
        async with Channel('localhost', 50051):
            stub = start_stop_writer_pb2_grpc.StartStopWriterStub(self.channel)
            self.responses = stub.ConnectDriver(self.execute_command())

            async for response in self.responses:
                print(time(), response)

    async def execute_command(self):
        while True:
            if self.command is None:
                await asyncio.sleep(0.5)
                continue

            command = self.command
            self.command = None
            print("Command:", command)

            yield start_stop_writer_pb2.WriterRequest(command)

    def start(self, request):
        if self.command is not None:
            raise RuntimeError("Command still in execution.")
        self.command = request

    def stop(self):
        pass

    def get_status(self):
        return self.status


# client = Client('localhost:50051')
# sleep(2)
# print(client.get_status())
# client.start({"something": "something"})
# sleep(1)
# print(client.get_status())
# input()
