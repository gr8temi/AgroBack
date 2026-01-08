import os
import socketio
from django.core.asgi import get_asgi_application
from config.socketio_app import sio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

# Import event handlers to register them
import reports.socket_events

application = socketio.ASGIApp(sio, django_asgi_app)
