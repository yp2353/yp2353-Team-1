from chatroom.routing import application as chatroom_application
from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": chatroom_application,
    }
)
