from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for the Product model (list view)."""
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'rating', 'description']
        read_only_fields = ['id']

class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for the Product model (detail view)."""
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id'] 