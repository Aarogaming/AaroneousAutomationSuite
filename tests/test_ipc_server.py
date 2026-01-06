import asyncio
import grpc
import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ipc.protos import bridge_pb2
from core.ipc.protos import bridge_pb2_grpc

async def test_ipc():
    """
    Integration test for the IPC server.
    """
    logger.info("Testing AAS IPC Server...")
    
    channel = grpc.aio.insecure_channel('localhost:50051')
    stub = bridge_pb2_grpc.BridgeStub(channel)
    
    try:
        # 1. Test ExecuteCommand
        logger.info("Sending test command...")
        response = await stub.ExecuteCommand(bridge_pb2.CommandRequest(
            command_type="TEST_PING",
            payload='{"data": "hello"}'
        ))
        logger.info(f"Response: {response.message} (Success: {response.success})")
        
        # 2. Test StreamSnapshots (briefly)
        logger.info("Testing snapshot stream (3 seconds)...")
        stream = stub.StreamSnapshots(bridge_pb2.SnapshotRequest(interval_ms=1000))
        
        async def read_stream():
            try:
                async for snapshot in stream:
                    logger.info(f"Received snapshot at {snapshot.timestamp}")
            except grpc.aio.AioRpcError as e:
                if e.code() == grpc.StatusCode.CANCELLED:
                    logger.info("Stream cancelled as expected.")
                else:
                    raise

        # Run stream reader for 3 seconds
        try:
            await asyncio.wait_for(read_stream(), timeout=3.0)
        except asyncio.TimeoutError:
            logger.info("Stream test timed out (Normal behavior).")
            
        logger.success("IPC Server integration test completed.")
        
    except Exception as e:
        logger.error(f"IPC test failed: {e}")
        logger.info("Ensure the IPC server is running: python core/main.py")
    finally:
        await channel.close()

if __name__ == "__main__":
    asyncio.run(test_ipc())
