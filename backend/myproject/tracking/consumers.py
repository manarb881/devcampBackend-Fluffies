
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from orders.models import Order, OrderTracking

class OrderTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.room_group_name = f'order_{self.order_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Check if user has permission to track this order
        has_permission = await self.check_permission()
        if not has_permission:
            await self.close()
            return
        
        await self.accept()
        
        # Send initial tracking data
        await self.send_tracking_data()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    @database_sync_to_async
    def check_permission(self):
        user = self.scope['user']
        try:
            order = Order.objects.get(id=self.order_id)
            return user.is_staff or order.user == user
        except Order.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_tracking_data(self):
        try:
            order = Order.objects.get(id=self.order_id)
            tracking_updates = OrderTracking.objects.filter(order=order).order_by('-timestamp')
            return {
                'order_id': order.id,
                'status': order.status,
                'tracking_updates': [
                    {
                        'id': update.id,
                        'status': update.status,
                        'location': update.location,
                        'latitude': update.latitude,
                        'longitude': update.longitude,
                        'description': update.description,
                        'timestamp': update.timestamp.isoformat(),
                    }
                    for update in tracking_updates
                ]
            }
        except Order.DoesNotExist:
            return None
    
    async def send_tracking_data(self):
        tracking_data = await self.get_tracking_data()
        if tracking_data:
            await self.send(text_data=json.dumps(tracking_data))
    
    async def receive(self, text_data):
        # Consumers can handle client requests here if needed
        pass
    
    async def tracking_update(self, event):
        # Send tracking update to WebSocket
        await self.send(text_data=json.dumps(event['data']))