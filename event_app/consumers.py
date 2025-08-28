import json
from channels.generic.websocket import AsyncWebsocketConsumer

class EventStatusConsumer(AsyncWebsocketConsumer):
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