# backend/predictions/serializers.py

from rest_framework import serializers
from .models import StockPrediction
from products.models import Product # Assuming products app exists

# Serializer for nested Product data representation
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name']
        read_only = True

# Serializer for StockPrediction
class StockPredictionSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True,
        required=True
    )
    date = serializers.DateField(
        write_only=True, # Only for input validation
        required=True
    )

    class Meta:
        model = StockPrediction
        fields = [
            'id', 'product', 'product_id',
            'week_number', 'month', 'store_id',
            'total_price', 'base_price', 'is_featured_sku', 'is_display_sku',
            'predicted_stock', 'created_at',
            'date', # Keep 'date' here so it's processed during validation
        ]
        read_only_fields = [
            'id', 'product', 'week_number', 'month',
            'predicted_stock', 'created_at'
        ]

    # --- Validation Methods (Keep as they were) ---
    def validate_total_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total price must be greater than 0.")
        return value

    def validate_base_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Base price must be greater than 0.")
        return value

    # --- ADD THIS OVERRIDE METHOD ---
    def create(self, validated_data):
        """
        Override the default create method to handle the 'date' field
        which is used for input but not stored on the model.
        """
        # The 'validated_data' here includes fields from the request
        # AND any extra kwargs passed to serializer.save() by the view
        # (like 'predicted_stock', 'week_number', 'month').

        # Remove the 'date' field before it's passed to the model's create method.
        validated_data.pop('date', None) # Safely remove 'date' if it exists

        # Now validated_data only contains fields that ARE valid
        # arguments for StockPrediction.objects.create()
        print(f"Data being passed to StockPrediction.objects.create: {validated_data}")
        instance = StockPrediction.objects.create(**validated_data)
        return instance
    # --- END OF OVERRIDE ---