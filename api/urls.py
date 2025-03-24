from django.urls import path
from .views import ProductListView, ProductDetailView, ScraperView, InsightsView

urlpatterns = [
    # API endpoints for products
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    
    # Scraper endpoint
    path('scrape/', ScraperView.as_view(), name='scrape'),
    
    # Insights endpoint
    path('insights/', InsightsView.as_view(), name='insights'),
] 