import socketio
import os
import sys

# Redis URL matches docker-compose
url = "redis://redis:6379/0"

print(f"Connecting to Redis at {url}")
mgr = socketio.RedisManager(url, write_only=True)

room = 'user_1'
print(f"Emitting to room: {room}")

try:
    # Mimic user's task code
    sio = socketio.Server(client_manager=mgr)
    sio.emit('notification', {'message': 'TEST MESSAGE via socketio.Server'}, room=room)
    print("Emitted successfully via socketio.Server")
except Exception as e:
    print(f"Emit failed: {e}")
