import asyncio
import grpc
from loguru import logger
from typing import AsyncIterable, Optional

# These will be generated from bridge.proto
try:
    from core.ipc.protos import bridge_pb2
    from core.ipc.protos import bridge_pb2_grpc
except ImportError:
    logger.warning("gRPC protos not found. Run scripts/generate_protos.py")
    bridge_pb2 = None
    bridge_pb2_grpc = object

class BridgeService(bridge_pb2_grpc.BridgeServicer if bridge_pb2_grpc != object else object):
    """
    Python implementation of the AAS <-> Maelstrom IPC Bridge.
    Handles high-level commands and game state snapshot streaming.
    """
    def __init__(self):
        self._latest_snapshot = None

    async def ExecuteCommand(self, request: 'bridge_pb2.CommandRequest', context: grpc.aio.ServicerContext) -> 'bridge_pb2.CommandResponse':
        logger.info(f"Received command from Maelstrom: {request.command_type}")
        # Logic to route command to AAS plugins
        return bridge_pb2.CommandResponse(success=True, message="Command received by AAS Hub")

    async def StreamSnapshots(self, request: 'bridge_pb2.SnapshotRequest', context: grpc.aio.ServicerContext) -> AsyncIterable['bridge_pb2.SnapshotResponse']:
        logger.info(f"Maelstrom requested snapshot stream at {request.interval_ms}ms")
        while True:
            if self._latest_snapshot:
                yield self._latest_snapshot
            await asyncio.sleep(request.interval_ms / 1000.0)

async def serve_ipc(port: int = 50051):
    server = grpc.aio.server()
    bridge_pb2_grpc.add_BridgeServicer_to_server(BridgeService(), server)
    server.add_insecure_port(f'[::]:{port}')
    logger.info(f"Starting AAS IPC Bridge on port {port}...")
    await server.start()
    await server.wait_for_termination()
