import asyncio
import grpc
import time
from loguru import logger
from typing import AsyncIterable, Optional, Set

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
        self._task_subscribers: Set[asyncio.Queue] = set()

    async def broadcast_task_update(self, task_id: str, title: str, status: str, assignee: str, event_type: str):
        """Broadcast a task update to all subscribers."""
        if not bridge_pb2:
            return

        update = bridge_pb2.TaskUpdate(
            task_id=task_id,
            title=title,
            status=status,
            assignee=assignee,
            event_type=event_type,
            timestamp=int(time.time())
        )
        
        for queue in self._task_subscribers:
            await queue.put(update)

    async def SubscribeToTasks(self, request: 'bridge_pb2.TaskSubscriptionRequest', context: grpc.aio.ServicerContext) -> AsyncIterable['bridge_pb2.TaskUpdate']:
        logger.info(f"Client {request.client_id} subscribed to task updates")
        queue = asyncio.Queue()
        self._task_subscribers.add(queue)
        try:
            while True:
                update = await queue.get()
                yield update
        finally:
            self._task_subscribers.remove(queue)
            logger.info(f"Client {request.client_id} unsubscribed from task updates")

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

async def serve_ipc(port: int = 50051, service: Optional[BridgeService] = None):
    server = grpc.aio.server()
    if service is None:
        service = BridgeService()
    bridge_pb2_grpc.add_BridgeServicer_to_server(service, server)
    server.add_insecure_port(f'[::]:{port}')
    logger.info(f"Starting AAS IPC Bridge on port {port}...")
    await server.start()
    await server.wait_for_termination()
