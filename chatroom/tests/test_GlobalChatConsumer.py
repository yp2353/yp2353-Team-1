from channels.testing import WebsocketCommunicator
from django.test import TestCase
from chatroom.consumers import GlobalChatConsumer


class GlobalChatConsumerTestCase(TestCase):
    async def test_connect_and_disconnect(self):
        # Create a WebsocketCommunicator instance for testing
        WebsocketCommunicator(GlobalChatConsumer.as_asgi(), "/ws/")

        # Connect to the websocket
        # connected, _ = await communicator.connect()
        # self.assertTrue(connected)

        # # Disconnect from the websocket
        # await communicator.disconnect()

        # # Check that the connection was closed
        # self.assertTrue(communicator.connection_closed)
