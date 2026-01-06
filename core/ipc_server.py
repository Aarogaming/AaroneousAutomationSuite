import asyncio
import grpc
import time
from loguru import logger
from typing import AsyncIterable, Optional, Set, Any
import json

from core.db_manager import get_db_manager
from core.db_repositories import ConfigRepository

# These will be generated from bridge.proto
try:
    from core.ipc.protos import bridge_pb2
    from core.ipc.protos import bridge_pb2_grpc
except ImportError:
    # Fallback for when protos are not yet generated
    bridge_pb2 = None
    bridge_pb2_grpc = object

class BridgeService(bridge_pb2_grpc.BridgeServicer if bridge_pb2 else object):
    """
    Python implementation of the AAS <-> Maelstrom IPC Bridge.
    Handles high-level commands and game state snapshot streaming.
    """
    def __init__(self, db_manager=None):
        self._latest_snapshot = None
        self._task_subscribers: Set[asyncio.Queue] = set()
        self._db_manager = db_manager or get_db_manager()

    async def GetConfig(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        """Retrieve configuration from the database."""
        if bridge_pb2 is None:
            return None

        logger.info(f"Config request received for key: {request.key or 'ALL'}")
        
        try:
            with self._db_manager.get_session() as session:
                configs = {}
                if request.key:
                    value = ConfigRepository.get(session, str(request.key))
                    if value is not None:
                        configs[str(request.key)] = json.dumps(value)
                else:
                    # Return all non-secret configs
                    all_entries = ConfigRepository.get_all(session)
                    for entry in all_entries:
                        if not bool(entry.is_secret):
                            value = ConfigRepository.get(session, str(entry.key))
                            configs[str(entry.key)] = json.dumps(value)
                
                return bridge_pb2.ConfigResponse(
                    success=True,
                    message="Configuration retrieved successfully",
                    configs=configs
                )
        except Exception as e:
            logger.error(f"Failed to get config: {e}")
            return bridge_pb2.ConfigResponse(success=False, message=str(e))

    async def SetConfig(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        """Update configuration in the database."""
        if bridge_pb2 is None:
            return None

        logger.info(f"Set config request for key: {request.key}")
        
        try:
            # Parse value based on type
            value: Any = request.value
            if str(request.value_type) == "int":
                value = int(request.value)
            elif str(request.value_type) == "bool":
                value = str(request.value).lower() in ("true", "1", "yes")
            elif str(request.value_type) == "json":
                value = json.loads(str(request.value))

            with self._db_manager.get_session() as session:
                ConfigRepository.set(
                    session,
                    key=str(request.key),
                    value=value,
                    value_type=str(request.value_type),
                    is_secret=bool(request.is_secret)
                )
                return bridge_pb2.ConfigResponse(
                    success=True,
                    message=f"Configuration {request.key} updated successfully"
                )
        except Exception as e:
            logger.error(f"Failed to set config: {e}")
            return bridge_pb2.ConfigResponse(success=False, message=str(e))

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

    async def SubscribeToTasks(self, request: Any, context: grpc.aio.ServicerContext) -> AsyncIterable[Any]:
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

    async def ExecuteCommand(self, request: Any, context: grpc.aio.ServicerContext) -> Any:
        if bridge_pb2 is None:
            return None
        logger.info(f"Received command from Maelstrom: {request.command_type}")
        # Logic to route command to AAS plugins
        return bridge_pb2.CommandResponse(success=True, message="Command received by AAS Hub")

    async def StreamSnapshots(self, request: Any, context: grpc.aio.ServicerContext) -> AsyncIterable[Any]:
        logger.info(f"Maelstrom requested snapshot stream at {request.interval_ms}ms")
        while True:
            if self._latest_snapshot:
                yield self._latest_snapshot
            await asyncio.sleep(request.interval_ms / 1000.0)

async def serve_ipc(port: int = 50051, service: Optional[BridgeService] = None):
    if not bridge_pb2:
        logger.warning("IPC Bridge cannot start: protos not found")
        return

    server = grpc.aio.server()
    if service is None:
        service = BridgeService()
    bridge_pb2_grpc.add_BridgeServicer_to_server(service, server)
    server.add_insecure_port(f'[::]:{port}')
    logger.info(f"Starting AAS IPC Bridge on port {port}...")
    await server.start()
    await server.wait_for_termination()
