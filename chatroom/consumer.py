# consumer.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import ChatMessage, RoomModel


class GlobalChatConsumer(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return JsonResponse({"error": "Method not allowed"}, status=405)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        message_type = data.get("type")

        if message_type == "join_room":
            room_id = data.get("roomID")
            sender = self.get_user()
            room_messages = self.retrieve_room_messages(room_id)
            messages = []

            for message in room_messages:
                sender_username = message.sender.username
                messages.append(
                    {
                        "type": "chat_message",
                        "message": message.content,
                        "sender": sender_username,
                    }
                )

            return JsonResponse({"messages": messages})

        elif message_type == "chat_message":
            room_id = data.get("roomID")
            message = data.get("message")
            sender = self.get_user()
            self.save_chat_db(sender, room_id, message)

            return JsonResponse({"success": True})

        return JsonResponse({"error": "Invalid request"})

    def retrieve_room_messages(self, room_id):
        room_messages = ChatMessage.objects.filter(room=room_id)
        return room_messages

    def save_chat_db(self, sender, room_id, message):
        message = ChatMessage.objects.create(
            sender=sender,
            room=RoomModel.objects.get(roomID=room_id),
            content=message,
        )
        message.save()
