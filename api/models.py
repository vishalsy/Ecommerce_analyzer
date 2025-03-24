from django.db import models

class Product(models.Model):
    """Model to store scraped product data from e-commerce websites."""
    
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - ${self.price}"
    
    class Meta:
        ordering = ['-id']

class ProductAnalysis(models.Model):
    """Model to store AI-generated analysis of products."""
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='analysis')
    summary = models.TextField()
    sentiment_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    keywords = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analysis for {self.product.name}"
    
    class Meta:
        verbose_name_plural = "Product analyses"

class Insight(models.Model):
    """Model to store overall insights generated from product data."""
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    insight_type = models.CharField(max_length=50)  # e.g., "trend", "pricing", "category"
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
