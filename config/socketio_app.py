import socketio
import os

# Create a Socket.IO server
# client_manager configures Redis for emitting events from external processes (Celery)
mgr = socketio.AsyncRedisManager("redis://redis:6379/0", write_only=False)

sio = socketio.AsyncServer(
    async_mode='asgi',
    client_manager=mgr,
    cors_allowed_origins='*'
)
