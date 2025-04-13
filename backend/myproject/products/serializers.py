from rest_framework import serializers
from .models import Category, Product, ProductImage

# Serializer for ProductImage
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text']

# Serializer for Category
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image']

# Serializer for Product List (short version for lists)
class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    imageUrl = serializers.SerializerMethodField()  # To ensure image URL is returned
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'imageUrl', 'category', 'category_name', 'available', 'stock']
    
    def get_imageUrl(self, obj):
        # Assuming you have a method for getting the URL of the image
        return obj.image.url if obj.image else None

# Serializer for Product Detail (full version for detailed view)
class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    imageUrl = serializers.SerializerMethodField()  # To return the URL of the image
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'price', 'imageUrl', 'category', 'stock', 'available', 'images', 'created_at']
    
    def get_imageUrl(self, obj):
        return obj.image.url if obj.image else None
