import os
import json
import django
import logging
from datetime import datetime

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce_analyzer.settings")
django.setup()

from api.models import Product

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('data_import')

def import_amazon_data(file_path='data/amazon_products.json'):
    """Import Amazon product data from a JSON file into the database."""
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        logger.info(f"Loaded {len(products)} products from {file_path}")
        
        # Track statistics
        products_added = 0
        products_updated = 0
        
        for product in products:
            # Extract product data
            name = product.get('name', 'Unknown Product')
            price = product.get('price', 0.0)
            description = product.get('description', '')
            rating = product.get('rating', 0.0)
            image_url = product.get('image_url', '')
            url = product.get('url', '')
            source = 'amazon'
            
            # Try to find existing product by URL
            existing_product = Product.objects.filter(url=url).first()
            
            if existing_product:
                # Update existing product
                existing_product.name = name
                existing_product.price = price
                existing_product.description = description
                existing_product.rating = rating
                existing_product.image_url = image_url
                existing_product.last_updated = datetime.now()
                existing_product.save()
                products_updated += 1
                logger.info(f"Updated product: {name}")
            else:
                # Create new product
                Product.objects.create(
                    name=name,
                    price=price,
                    description=description,
                    rating=rating,
                    image_url=image_url,
                    url=url,
                    source=source
                )
                products_added += 1
                logger.info(f"Added new product: {name}")
        
        logger.info(f"Import complete: {products_added} products added, {products_updated} products updated")
        return products_added, products_updated
    
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        return 0, 0

def main():
    """Run the data import process."""
    logger.info("Starting data import process")
    import_amazon_data()
    logger.info("Data import process completed")

if __name__ == "__main__":
    main() 