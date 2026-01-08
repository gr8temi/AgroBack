from config.socketio_app import sio
from rest_framework_simplejwt.tokens import AccessToken
from core.models import User
from channels.db import database_sync_to_async
import urllib.parse

@database_sync_to_async
def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        return User.objects.get(id=access_token['user_id'])
    except Exception:
        return None

@sio.event
async def connect(sid, environ):
    # Extract token from query string
    # environ['QUERY_STRING'] might look like 'token=...'
    query_string = environ.get('QUERY_STRING', '')
    params = urllib.parse.parse_qs(query_string)
    token = params.get('token', [None])[0]
    
    if token:
        user = await get_user_from_token(token)
        if user:
            # Join a room named after user ID
            await sio.enter_room(sid, f"user_{user.id}")
            print(f"User {user.username} connected (sid: {sid})")
            await sio.emit('notification', {'message': 'Welcome to the Farm Management System!'}, room=f"user_{user.id}")
            return
    
    # If no valid token, maybe allow connection but no room? 
    # Or reject. Let's reject for now if strict.
    # print("Unauthenticated connection rejected")
    # return False # Reject
    print(f"Anonymous connected (sid: {sid})")
    await sio.emit('notification', {'message': 'Welcome to the Farm Management System!'}, room=f"user_{user.id}")

@sio.event
async def disconnect(sid):
    print(f"Disconnected (sid: {sid})")
