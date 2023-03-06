import asyncio
import logging

import grpc

from std_daq_service.writer_driver.start_stop import start_stop_writer_pb2_grpc, start_stop_writer_pb2


class StartStopWriterServicer(start_stop_writer_pb2_grpc.StartStopWriterServicer):
    async def read_client_requests(self, request_iter):
        async for client_update in request_iter:
            print("Recieved message from client:", client_update, end="")

    async def write_server_responses(self, context):
        while True:
            await context.write(start_stop_writer_pb2.WriterStatus())
            await asyncio.sleep(0.5)

    async def ConnectDriver(self, request_iter, context):
        write_task = asyncio.create_task(self.write_server_responses(context))
        read_task = asyncio.create_task(self.read_client_requests(request_iter))

        await write_task
        await read_task


async def main():
    server = grpc.aio.server()
    start_stop_writer_pb2_grpc.add_StartStopWriterServicer_to_server(StartStopWriterServicer(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    await server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    asyncio.run(main())
