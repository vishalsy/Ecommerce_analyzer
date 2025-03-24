from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'rating')
    list_filter = ('rating',)
    search_fields = ('name', 'description')
