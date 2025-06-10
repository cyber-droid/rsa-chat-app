import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, ChatRoom, User
from .encryption import encrypt_message, decrypt_message
from datetime import datetime

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')
        username = text_data_json.get('username', self.scope['user'].username)
        timestamp = text_data_json.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        is_history = text_data_json.get('is_history', False)
        is_typing = text_data_json.get('is_typing', False)

        if is_typing:
            # Broadcast typing event to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_event',
                    'username': username
                }
            )
        elif is_history:
            # For history messages, the message is already encrypted; just broadcast it
            recipient = 'user_b' if username == 'user_a' else 'user_a'
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,  # Already encrypted
                    'username': username,
                    'recipient': recipient,
                    'timestamp': timestamp,
                    'is_history': True
                }
            )
        else:
            # For new messages, encrypt and save as before
            try:
                recipient = 'user_b' if username == 'user_a' else 'user_a'
                recipient_user = await self.get_user(recipient)
                encrypted_message = encrypt_message(message, recipient_user.public_key)

                # Generate a timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Save the encrypted message to the database
                await self.save_message(username, self.room_name, encrypted_message, timestamp)

                # Send the encrypted message to the room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': encrypted_message,
                        'username': username,
                        'recipient': recipient,
                        'timestamp': timestamp,
                        'is_history': False
                    }
                )
            except ValueError as e:
                print(f"Encryption error: {str(e)}")
                await self.send(text_data=json.dumps({
                    'error': f"Failed to send message: {str(e)}"
                }))

    async def chat_message(self, event):
        encrypted_message = event['message']
        username = event['username']
        recipient = event['recipient']
        timestamp = event['timestamp']
        is_history = event.get('is_history', False)

        # Only attempt decryption if the current user is the intended recipient
        if self.scope['user'].username != recipient:
            return

        try:
            user = await self.get_user(self.scope['user'].username)
            decrypted_message = decrypt_message(encrypted_message, user.private_key)

            await self.send(text_data=json.dumps({
                'message': decrypted_message,
                'username': username,
                'timestamp': timestamp,
                'is_history': is_history
            }))
        except ValueError as e:
            print(f"Decryption error: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': f"Failed to decrypt message: {str(e)}"
            }))

    async def typing_event(self, event):
        # Send typing event to the client
        await self.send(text_data=json.dumps({
            'is_typing': True,
            'username': event['username']
        }))

    @database_sync_to_async
    def get_user(self, username):
        return User.objects.get(username=username)

    @database_sync_to_async
    def save_message(self, username, room_name, message, timestamp):
        user = User.objects.get(username=username)
        room, created = ChatRoom.objects.get_or_create(name=room_name)
        Message.objects.create(
            user=user,
            room=room,
            content=message,
            timestamp=timestamp
        )