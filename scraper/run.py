#!/usr/bin/env python3
"""
Runner script for the Amazon scraper.
"""

import os
import argparse
from scraper import EcommerceScraper
from import_data import import_products

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Amazon scraper')
    parser.add_argument('--max-products', type=int, default=200,
                        help='Maximum number of products to scrape')
    parser.add_argument('--output-dir', default='data',
                        help='Directory to store scraped data')
    parser.add_argument('--delay', type=float, default=2,
                        help='Delay between requests in seconds')
    parser.add_argument('--import', dest='do_import', action='store_true',
                        help='Import scraped data into the database')
    return parser.parse_args()

def get_amazon_config():
    """Get configuration for Amazon scraping."""
    return {
        'base_url': 'https://www.amazon.com',
        'categories': [
            'https://www.amazon.com/s?k=laptops',
            'https://www.amazon.com/s?k=smartphones',
            'https://www.amazon.com/s?k=headphones'
        ]
    }

def main():
    """Run the scraper."""
    args = parse_args()
    
    # Get Amazon configuration
    config = get_amazon_config()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize and run the scraper
    scraper = EcommerceScraper(
        base_url=config['base_url'],
        output_dir=args.output_dir,
        delay=args.delay
    )
    
    print(f"Scraping {args.max_products} products from Amazon...")
    scraper.scrape_products(
        category_urls=config['categories'],
        max_products=args.max_products
    )
    
    # Import data if requested
    if args.do_import:
        print("Importing scraped data into the database...")
        json_file = os.path.join(args.output_dir, 'amazon_products.json')
        import_products(json_file)
    
    print("Done!")

if __name__ == "__main__":
    main() 