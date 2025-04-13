from rest_framework import serializers
from .models import Order, OrderItem, OrderTracking
from products.models import Product
from products.serializers import ProductListSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'price', 'quantity']
        read_only_fields = ['price']
    
    def create(self, validated_data):
        product_id = validated_data.pop('product_id')
        product = Product.objects.get(id=product_id)
        validated_data['product'] = product
        validated_data['price'] = product.price
        return OrderItem.objects.create(**validated_data)

class OrderTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTracking
        fields = ['id','description', 'timestamp','status','location']
        read_only_fields = ['timestamp']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tracking = OrderTrackingSerializer(source='tracking_updates', many=True, read_only=True)
    items_data = serializers.ListField(
        write_only=True,
        child=serializers.DictField(child=serializers.Field())
    )
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'first_name', 'last_name', 'email', 'address', 'city', 
            'state', 'postal_code', 'country', 'phone', 'status', 'shipping_cost', 
            'total_cost', 'notes', 'created_at', 'updated_at', 'items_count', 
            'products_cost', 'items', 'tracking', 'items_data'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'items_count', 'products_cost', 'total_cost']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items_data')
        
        # Calculate total cost
        total_cost = 0
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            total_cost += product.price * item_data['quantity']
        
        # Add shipping cost to total
        shipping_cost = validated_data.get('shipping_cost', 0)
        total_cost += shipping_cost
        validated_data['total_cost'] = total_cost
        
        # Create order
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=item_data['quantity']
            )
        
        # Create initial tracking entry
        OrderTracking.objects.create(
            order=order,
            status=order.status,
            location='Order Processing Center',
            description='Order has been received and is being processed.'
        )
        
        return order