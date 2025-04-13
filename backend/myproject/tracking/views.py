from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from orders.models import Order, OrderTracking
from orders.serializers import OrderTrackingSerializer

class TrackOrder(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            # Check if user has permission to track this order
            order = Order.objects.get(id=order_id)
            if not request.user.is_staff and order.user != request.user:
                return Response({'error': 'You do not have permission to track this order.'}, 
                               status=status.HTTP_403_FORBIDDEN)
            
            # Get tracking updates
            tracking_updates = OrderTracking.objects.filter(order=order).order_by('-timestamp')
            serializer = OrderTrackingSerializer(tracking_updates, many=True)
            
            return Response({
                'order_id': order.id,
                'status': order.status,
                'tracking_updates': serializer.data
            })
            
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, order_id):
        # Only admin users can post tracking updates
        if not request.user.is_staff:
            return Response({'error': 'Only admin users can update tracking information.'},
                          status=status.HTTP_403_FORBIDDEN)
        
        try:
            order = Order.objects.get(id=order_id)
            serializer = OrderTrackingSerializer(data=request.data)
            
            if serializer.is_valid():
                tracking_update = serializer.save(order=order)
                
                # Update order status if changed
                new_status = serializer.validated_data.get('status')
                if new_status and new_status != order.status:
                    order.status = new_status
                    order.save()
                
                # Send real-time update to connected WebSocket clients
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'order_{order_id}',
                    {
                        'type': 'tracking_update',
                        'data': {
                            'order_id': order.id,
                            'status': order.status,
                            'tracking_update': {
                                'id': tracking_update.id,
                                'status': tracking_update.status,
                                'location': tracking_update.location,
                                'latitude': tracking_update.latitude,
                                'longitude': tracking_update.longitude,
                                'description': tracking_update.description,
                                'timestamp': tracking_update.timestamp.isoformat(),
                            }
                        }
                    }
                )
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)