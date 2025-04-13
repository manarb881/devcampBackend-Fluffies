
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Order, OrderItem, OrderTracking
from .serializers import OrderSerializer, OrderItemSerializer, OrderTrackingSerializer
from products.models import Product

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.is_staff:
            return True
        # Allow owners of the order
        return obj.user == request.user

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'updated_at', 'total_cost']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_tracking(self, request, pk=None):
        order = self.get_object()
        serializer = OrderTrackingSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(order=order)
            
            # Update order status if it has changed
            new_status = serializer.validated_data.get('status')
            if new_status and new_status != order.status:
                order.status = new_status
                order.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        # Only allow cancellation if the order is pending or processing
        if order.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Cannot cancel an order that has been shipped or delivered.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        # Add tracking entry for cancellation
        OrderTracking.objects.create(
            order=order,
            status='cancelled',
            location='Customer Service',
            description='Order has been cancelled by the customer.'
        )
        
        return Response({'status': 'Order cancelled successfully.'})