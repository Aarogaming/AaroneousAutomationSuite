import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws/events"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # Wait for a broadcast message
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received event: {data['event_type']} for task {data['task_id']}")
                if data['event_type'] == 'COMPLETED' and data['task_id'] == 'AAS-119':
                    print("Success: Received completion event!")
                    break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
