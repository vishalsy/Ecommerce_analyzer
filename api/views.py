import os
import json
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from openai import OpenAI
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer, ProductDetailSerializer
from scraper.scraper import EcommerceScraper

logger = logging.getLogger(__name__)

from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Min, Max, Count, Q
from django.shortcuts import get_object_or_404

class ProductListView(APIView):
    """API view for listing products."""
    
    def get(self, request):
        """Get a list of products with pagination."""
        try:
            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Get all products
            products = Product.objects.all().order_by('-id')
            
            # Calculate pagination
            start = (page - 1) * page_size
            end = start + page_size
            
            # Get paginated products
            paginated_products = products[start:end]
            
            # Serialize the products
            serializer = ProductSerializer(paginated_products, many=True)
            
            # Prepare response with pagination info
            return Response({
                'count': products.count(),
                'next': f'/api/products/?page={page+1}&page_size={page_size}' if end < products.count() else None,
                'previous': f'/api/products/?page={page-1}&page_size={page_size}' if page > 1 else None,
                'results': serializer.data
            })
            
        except ValueError as e:
            return Response({
                'error': 'Invalid pagination parameters',
                'detail': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Error in product list view: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'detail': str(e)
            }, status=500)

class ProductDetailView(APIView):
    """API view for retrieving product details."""
    
    def get(self, request, pk):
        """Get detailed information about a specific product."""
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)

class ProductStatsView(APIView):
    """
    API endpoint for product statistics.
    """
    
    def get(self, request, format=None):
        """Return product statistics."""
        stats = {
            'total_products': Product.objects.count(),
            'avg_price': Product.objects.aggregate(Avg('price'))['price__avg'],
            'avg_rating': Product.objects.aggregate(Avg('rating'))['rating__avg'],
            'price_range': {
                'min': Product.objects.aggregate(Min('price'))['price__min'],
                'max': Product.objects.aggregate(Max('price'))['price__max'],
            },
            'rating_distribution': self._get_rating_distribution()
        }
        return Response(stats)
    
    def _get_rating_distribution(self):
        """Get the distribution of product ratings."""
        distribution = {}
        for i in range(1, 6):  # Ratings 1-5
            count = Product.objects.filter(rating__gte=i, rating__lt=i+1).count()
            distribution[f"{i} stars"] = count
        return distribution

@method_decorator(csrf_exempt, name='dispatch')
class ScraperView(View):
    """View for triggering the Amazon product scraper."""
    
    def post(self, request):
        """Start a scraping job for Amazon products."""
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            categories = data.get('categories', [])  # Now expecting category names
            max_products = data.get('max_products', 100)
            
            # Validate parameters
            if not categories:
                return JsonResponse({
                    'error': 'No categories provided',
                    'status': 'error'
                }, status=400)
            
            # Validate max_products
            try:
                max_products = int(max_products)
                if max_products <= 0:
                    return JsonResponse({
                        'error': 'max_products must be a positive number',
                        'status': 'error'
                    }, status=400)
                if max_products > 500:  # Set a reasonable upper limit
                    logger.warning(f"Large max_products value requested: {max_products}, capping at 500")
                    max_products = 500
            except (ValueError, TypeError):
                return JsonResponse({
                    'error': 'max_products must be a valid number',
                    'status': 'error'
                }, status=400)
            
            # Build Amazon search URLs from categories
            category_urls = []
            for category in categories:
                # Replace spaces with plus signs for URL formatting
                formatted_category = category.strip().replace(' ', '+')
                amazon_url = f"https://www.amazon.com/s?k={formatted_category}"
                category_urls.append(amazon_url)
            
            logger.info(f"Starting Amazon scraper for categories: {', '.join(categories)}, max_products={max_products}")
            
            # Initialize scraper for Amazon
            scraper = EcommerceScraper(
                base_url='https://www.amazon.com',
                output_dir='data',
                delay=2
            )
            
            # Execute the scraper
            products = scraper.scrape_products(category_urls, max_products=max_products)
            
            # Import the data using the import script
            from scraper.import_data import import_amazon_data
            products_added, products_updated = import_amazon_data()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Scraping completed. Added {products_added} products, updated {products_updated} products.',
                'products_found': len(products),
                'max_products': max_products,
                'categories': categories
            })
            
        except Exception as e:
            logger.error(f"Error in scraper view: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class InsightsView(View):
    """View for providing AI-powered insights about products."""
    
    def get_api_key(self):
        """Get the OpenAI API key from environment variables."""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI API key not found in environment variables")
            return None
        return api_key
    
    def generate_answer(self, question, product=None):
        """Generate an AI answer using OpenAI."""
        api_key = self.get_api_key()
        if not api_key:
            return {
                'error': 'OpenAI API key not configured.',
                'status': 'error'
            }
        
        try:
            client = OpenAI(api_key=api_key)
            
            if product:
                # Format product data as context
                context = (
                    f"Product: {product.name}\n"
                    f"Price: ${product.price}\n"
                    f"Rating: {product.rating}/5\n"
                    f"Description: {product.description}\n"
                )
                prompt = f"Based on this product information:\n\n{context}\n\nQuestion: {question}\n\nAnswer:"
            else:
                # General question about products in the database
                products = Product.objects.all()[:5]  # Limit to 5 products for context
                context = "Products in the database:\n\n"
                for p in products:
                    context += f"- {p.name} (${p.price}): {p.description[:100]}...\n"
                
                prompt = f"Based on these products:\n\n{context}\n\nQuestion: {question}\n\nAnswer:"
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful e-commerce assistant that provides insights about products."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                'answer': answer,
                'status': 'success',
                'provider': 'openai'
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                'error': f"Error generating answer: {str(e)}",
                'status': 'error'
            }
    
    def post(self, request):
        """Process an insights request."""
        try:
            data = json.loads(request.body)
            question = data.get('question')
            product_id = data.get('product_id')
            
            if not question:
                return JsonResponse({
                    'error': 'No question provided',
                    'status': 'error'
                }, status=400)
            
            # Get product if ID is provided
            product = None
            if product_id:
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    return JsonResponse({
                        'error': f'Product with ID {product_id} not found',
                        'status': 'error'
                    }, status=404)
            
            # Generate answer
            result = self.generate_answer(question, product)
            
            # Log the interaction
            if product:
                logger.info(f"Insights request for product {product.id}: '{question}'")
            else:
                logger.info(f"General insights request: '{question}'")
            
            # Return the result
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error in insights view: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)
