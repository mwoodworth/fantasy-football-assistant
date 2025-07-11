#!/usr/bin/env python3
"""Test WebSocket connection to verify it's working."""

import asyncio
import socketio
import sys

# Create Socket.IO client
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("✅ Connected to WebSocket server!")
    
    # Try to join a test draft session
    await sio.emit('join_draft_session', {
        'user_id': '1',
        'draft_session_id': 'test123'
    })

@sio.event
async def disconnect():
    print("❌ Disconnected from server")

@sio.event
async def connected(data):
    print(f"📨 Received 'connected' event: {data}")

@sio.event
async def joined_draft(data):
    print(f"✅ Successfully joined draft: {data}")
    print("\n🎉 WebSocket server is working properly!")
    
    # Test complete, disconnect
    await sio.disconnect()

@sio.event
async def error(data):
    print(f"❌ Error: {data}")

@sio.event
async def draft_update(data):
    print(f"📊 Draft update: {data}")

async def main():
    try:
        print("🔌 Attempting to connect to WebSocket server at http://localhost:8000...")
        await sio.connect('http://localhost:8000', 
                         transports=['websocket', 'polling'],
                         socketio_path='/socket.io')
        
        # Wait a bit for events
        await asyncio.sleep(3)
        
        if sio.connected:
            await sio.disconnect()
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print("\nMake sure the backend server is running:")
        print("  cd /home/mwoodworth/code/my-projects/fantasy-football-assistant")
        print("  python3 -m src.main")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())