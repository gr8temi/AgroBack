from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from core.models import User

@database_sync_to_async
def get_user(token_key):
    try:
        access_token = AccessToken(token_key)
        user = User.objects.get(id=access_token['user_id'])
        return user
    except Exception:
        return AnonymousUser()

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        query_params = dict(qp.split('=') for qp in query_string.split('&') if '=' in qp)
        token = query_params.get('token')
        
        if token:
            scope['user'] = await get_user(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await self.inner(scope, receive, send)
