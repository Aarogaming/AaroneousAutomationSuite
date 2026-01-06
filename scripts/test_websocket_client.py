import asyncio
import websockets
import json
import sys

async def listen():
    uri = "ws://localhost:8000/ws/events"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for events...")
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"\n🔔 [EVENT] {data.get('event_type')}")
                print(f"   Task: {data.get('task_id')} - {data.get('title')}")
                print(f"   Status: {data.get('status')} | Assignee: {data.get('assignee')}")
                print(f"   Time: {data.get('timestamp')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        print("\nStopped.")
