import json
from channels.generic.websocket import WebsocketConsumer
from offer.models import User


class TextRoomConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs']['user_id']
        user = User.objects.get(user_id=user_id)
        user.user_channel_name = self.channel_name
        user.save()
        self.user_id = user_id
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        print("Disconnected")
        user = User.objects.get(user_id=self.user_id)
        user.user_channel_name = 'nc'
        user.save()

    def receive(self, text_data):
        # Receive message from WebSocket
        text_data_json = json.loads(text_data)
        data = text_data_json['data']
        print(data)

    def create_session(self, event):
        # Receive message from room group
        session = event['session']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'responseType': 'sessionCreated',
            'session': session
        }))

    def send_message(self, event):
        # Receive message from room group
        message = event['message']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'responseType': 'messageSent',
            'message': message
        }))

    def close_session(self, event):
        # Receive message from room group
        session = event['session']
        # Send message to WebSocket
        print("HERE")
        self.send(text_data=json.dumps({
            'responseType': 'sessionClosed',
            'session': session
        }))
