import json
from channels.generic.websocket import WebsocketConsumer

class EventStatusConsumer(WebsocketConsumer):
    async def connect(self):
        self.organizer_id = self.scope['user'].id
        self.group_name = f'organizer_{self.organizer_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name,)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    
    async def receive(self, text_data):
        # handle message from frontend
        password
    
    async def event_status_update(self, event):
        await self.send(text_data=json.dumps(event))

class AdminNotificationConsumer(WebsocketConsumer):
    async def connect(self):
        self.group_name = 'admin_group'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_event_notification(self, event):
        await self.send(text_data=json.dumps(event))

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        if self.scope['user'].is_authenticated:
            print('Connected')
            self.group_name = f'user_{self.scope["user"].id}'
            self.channel_layer.group_add(self.group_name, self.channel_name)
            self.accept()
        else:
            self.close()
        
    def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            self.channel_laye.group_discard(self.group_name, self.channel_name)

    def receive(self, text_data):
        pass
    
    def send_notification(self, event):
        self.send(text_data=json.dumps({
            'message': event['message'],
            'url': event.get('url'),
            'created_at': event.get('created_at'),
        }))