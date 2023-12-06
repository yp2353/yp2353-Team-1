import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chatroom.views import get_user_exist


class GlobalChatConsumer(AsyncWebsocketConsumer):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.roomID = "default"
        self.sender = None
        self.message = ""

    async def connect(self):
        user_id = self.scope["session"].get("user_id")
        self.sender = await self.get_user(user_id)
        print("USER ----> $", self.sender)

        await self.channel_layer.group_add(self.roomID, self.channel_name)
        await self.accept()
        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.roomID, self.channel_name)

    async def receive(self, text_data):
        user_id = self.scope["session"].get("user_id")
        self.sender = await self.get_user(user_id)
        print("USER ----> $", self.sender)
        
        text_data_json = json.loads(text_data)

        message_type = text_data_json.get("type")
        self.message = text_data_json.get("message")

        print("Message type", message_type)
        

        if message_type == "join_room":
            self.roomID = text_data_json.get("roomID")
            print("Joining Room -> ", self.roomID)
            await self.channel_layer.group_add(self.roomID, self.channel_name)

            messages = await self.retrieve_room_messages(self.roomID)

            await self.send(
                text_data=json.dumps(
                    {"type": "info", "message": f"You have joined room {self.roomID}"}
                )
            )
            async for message in messages:
                sender_username = await database_sync_to_async(
                    lambda: message.sender.username
                )()
                sender_id = await database_sync_to_async(
                    lambda: message.sender.user_id
                )()
                
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "chat_message",
                            "message": message.content,
                            "sender": sender_username,
                            "sender_id": sender_id,
                            "current_user_id": self.sender.user_id,
                        }
                    )
                )
        elif message_type == "chat_message":
            print("========insied receive func========")
            await self.save_chat_db()
            await self.channel_layer.group_send(
            self.roomID,
            {
                "type": "chat_message",
                "message": self.message,
                "sender": self.sender.username,
                "roomID": self.roomID,  # Include roomID in the event payload
                "sender_id": self.sender.user_id,
            },    
        )
        elif message_type == "get_user_id":
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "user_id",
                        "user_id": self.sender.user_id,  
                    }
                )
            )


    async def chat_message(self, event):
        print("++++++insied chatmessage func+++++")
        message = event["message"]
        sender = event["sender"]
        sender_id = event["sender_id"]  
        room_id = event["roomID"]

        if self.roomID == room_id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "chat_message",
                        "message": message,
                        "sender": sender,
                        "sender_id": sender_id,  
                    }
                )
            )
                

    @database_sync_to_async
    def get_user(self, user_id):
        user = get_user_exist(user_id)
        return user

    @database_sync_to_async
    def retrieve_room_messages(self, roomID):
        from chatroom.models import ChatMessage

        room_messages = ChatMessage.objects.filter(room=roomID).order_by('timestamp').distinct()
        return room_messages

    async def save_chat_db(self):
        from chatroom.models import ChatMessage, RoomModel

        user_id = self.scope["session"].get("user_id")
        self.sender = await self.get_user(user_id)

        print("Before saving  room = ",self.roomID, " ,user = " , self.sender)

        if self.sender:
            room = await database_sync_to_async(RoomModel.objects.get)(
                roomID=self.roomID
            )

            message = await database_sync_to_async(ChatMessage.objects.create)(
                sender=self.sender,
                room=room,
                content=self.message,
            )
            await database_sync_to_async(message.save)()
