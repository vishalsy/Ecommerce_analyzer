import os
import time
import json
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('amazon_scraper')

class EcommerceScraper:
    """A scraper for Amazon to extract product data."""
    
    def __init__(self, base_url='https://www.amazon.com', output_dir='data', delay=2):
        """Initialize the scraper with the given parameters."""
        self.base_url = base_url
        self.output_dir = output_dir
        self.delay = delay
        
        # More realistic browser headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Initialize session with retry logic
        self.session = self._create_session()
        
        # Add cookies for session
        self.session.cookies.update({
            'session-id': f'{random.randint(100000000, 999999999)}',
            'session-token': f'{random.randint(10000000, 99999999)}-{random.randint(1000000, 9999999)}'
        })
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Initialized Amazon scraper for {self.base_url}")
    
    def _create_session(self):
        """Create a session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=5,  # number of retries
            backoff_factor=0.5,  # wait 0.5, 1, 2, 4, 8 seconds between retries
            status_forcelist=[500, 502, 503, 504],  # HTTP status codes to retry on
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self.headers)
        return session
    
    def _check_internet_connection(self):
        """Check if there's an active internet connection."""
        try:
            # Try to connect to a reliable host
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    def _get_page(self, url):
        """Fetch a page and return the BeautifulSoup object."""
        if not self._check_internet_connection():
            logger.error("No internet connection available")
            return None
            
        try:
            # Random delay between requests
            random_delay = self.delay * (1 + random.uniform(-0.2, 0.5))
            time.sleep(random_delay)
            
            logger.info(f"Fetching {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Check if we got a valid response
            if 'Robot Check' in response.text or 'captcha' in response.text.lower():
                logger.error("Amazon is requesting verification. Try again later.")
                return None
                
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def scrape_product_links(self, category_url, num_pages=5):
        """Scrape product links from Amazon category pages."""
        product_links = []
        
        # Amazon selectors
        amazon_selectors = {
            'product_card': 'div[data-component-type="s-search-result"]',
            'link_attr': 'data-asin',
            'link_selector': '.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal',
            'title_selector': '.a-size-medium.a-color-base.a-text-normal',
            'next_page': '.s-pagination-next',
        }
        
        logger.info(f"Using Amazon selectors to scrape: {category_url}")
        
        for page in range(1, num_pages + 1):
            # Adjust URL for pagination
            if page > 1:
                page_url = f"{category_url}&page={page}"
            else:
                page_url = category_url
            
            soup = self._get_page(page_url)
            if not soup:
                continue
            
            # Get product cards
            product_cards = soup.select(amazon_selectors['product_card'])
            logger.info(f"Found {len(product_cards)} product cards on page {page}")
            
            # Process Amazon product cards
            for i, card in enumerate(product_cards):
                # Try different methods to extract product links
                
                # Method 1: Standard link
                link_element = card.select_one(amazon_selectors['link_selector'])
                if link_element and link_element.has_attr('href'):
                    link = link_element['href']
                    absolute_url = urljoin(self.base_url, link)
                    product_links.append(absolute_url)
                    logger.info(f"Found product link: {absolute_url}")
                    continue
                
                # Method 2: Title link
                if amazon_selectors['title_selector']:
                    title_element = card.select_one(amazon_selectors['title_selector'])
                    if title_element and title_element.parent and title_element.parent.has_attr('href'):
                        link = title_element.parent['href']
                        absolute_url = urljoin(self.base_url, link)
                        product_links.append(absolute_url)
                        logger.info(f"Found product link via title: {absolute_url}")
                        continue
                
                # Method 3: ASIN
                if amazon_selectors['link_attr'] in card.attrs:
                    asin = card.get(amazon_selectors['link_attr'])
                    if asin:
                        absolute_url = f"https://www.amazon.com/dp/{asin}"
                        product_links.append(absolute_url)
                        logger.info(f"Found product link from ASIN: {absolute_url}")
                        continue
                
                # Method 4: Any link
                any_links = card.select('a')
                for a_link in any_links:
                    if a_link.has_attr('href') and ('/dp/' in a_link['href'] or '/gp/product/' in a_link['href']):
                        link = a_link['href']
                        absolute_url = urljoin(self.base_url, link)
                        product_links.append(absolute_url)
                        logger.info(f"Found product link: {absolute_url}")
                        break
            
            logger.info(f"Scraped {len(product_cards)} products from page {page}")
            
            # Stop if we've scraped enough products
            if len(product_links) >= 200:
                logger.info(f"Reached product limit, stopping pagination")
                break
            
            # Check if there's a next page
            next_page = soup.select_one(amazon_selectors['next_page'])
            if not next_page or 'a-disabled' in next_page.get('class', []):
                logger.info(f"No more pages available after page {page}")
                break
        
        logger.info(f"Total product links found: {len(product_links)}")
        return product_links
    
    def scrape_product_details(self, product_url):
        """Scrape details from an Amazon product page."""
        soup = self._get_page(product_url)
        if not soup:
            return None
        
        # Amazon selectors
        amazon_selectors = {
            'name': '#productTitle',
            'price': '.a-price .a-offscreen',
            'description': '#productDescription, #feature-bullets',
            'rating': '.a-star-rating-wrapper .a-icon-alt, .a-icon-star-small .a-icon-alt',
            'reviews': '#acrCustomerReviewText',
            'image': '#landingImage'
        }
        
        logger.info(f"Scraping product details: {product_url}")
        
        try:
            # Extract product details
            name = None
            for selector in amazon_selectors['name'].split(','):
                name_element = soup.select_one(selector.strip())
                if name_element:
                    name = name_element.get_text(strip=True)
                    logger.info(f"Found product name: {name[:50]}...")
                    break
            
            price = None
            for selector in amazon_selectors['price'].split(','):
                price_text = self._extract_text(soup, selector.strip())
                if price_text:
                    # Extract numerical value from price text
                    price = ''.join([c for c in price_text if c.isdigit() or c == '.'])
                    try:
                        price = float(price)
                        logger.info(f"Found product price: ${price}")
                        break
                    except ValueError:
                        continue
            
            description = None
            for selector in amazon_selectors['description'].split(','):
                description = self._extract_text(soup, selector.strip())
                if description:
                    logger.info(f"Found product description: {description[:50]}...")
                    break
            
            rating = None
            for selector in amazon_selectors['rating'].split(','):
                rating_text = self._extract_text(soup, selector.strip())
                if rating_text:
                    # Extract numerical rating
                    import re
                    rating_match = re.search(r'([0-9.]+)', rating_text)
                    if rating_match:
                        try:
                            rating = float(rating_match.group(1))
                            if rating > 5:  # Normalize to 5-star scale
                                rating = rating / 20
                            logger.info(f"Found product rating: {rating}")
                            break
                        except ValueError:
                            continue
            
            # Extract image URL
            image_url = None
            image_element = soup.select_one(amazon_selectors['image'])
            if image_element and image_element.has_attr('src'):
                image_url = image_element['src']
                logger.info(f"Found product image: {image_url[:50]}...")
            
            # Build the product object
            product = {
                'name': name if name else "Unknown Product",
                'price': price if price is not None else 0.0,
                'description': description if description else "",
                'rating': rating if rating is not None else 0.0,
                'image_url': image_url,
                'url': product_url,
                'source': 'amazon',
                'scraped_at': datetime.now().isoformat()
            }
            
            logger.info(f"Scraped details for Amazon product: {name}")
            return product
            
        except Exception as e:
            logger.error(f"Error scraping product details from {product_url}: {e}")
            return None
    
    def _extract_text(self, soup, selector, default=''):
        """Extract text from an element."""
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else default
    
    def scrape_products(self, category_urls, max_products=200):
        """Scrape products from Amazon categories up to a maximum number."""
        all_products = []
        
        for category_url in category_urls:
            # Calculate how many pages to scrape
            products_per_page = 20
            pages_needed = min(5, max_products // products_per_page)
            
            product_links = self.scrape_product_links(category_url, num_pages=pages_needed)
            
            # Take a random sample if we have more links than needed
            remaining_products = max_products - len(all_products)
            if len(product_links) > remaining_products:
                product_links = random.sample(product_links, remaining_products)
            
            # Scrape details for each product
            for link in product_links:
                product = self.scrape_product_details(link)
                if product:
                    all_products.append(product)
                
                if len(all_products) >= max_products:
                    break
            
            if len(all_products) >= max_products:
                break
        
        logger.info(f"Scraped a total of {len(all_products)} Amazon products")
        
        # Save products to a JSON file
        output_path = os.path.join(self.output_dir, 'amazon_products.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved Amazon product data to {output_path}")
        return all_products

def main():
    """Run the Amazon scraper."""
    base_url = "https://www.amazon.com"
    scraper = EcommerceScraper(base_url, output_dir='data', delay=2)
    
    category_urls = [
        "https://www.amazon.com/s?k=laptops",
        "https://www.amazon.com/s?k=smartphones",
        "https://www.amazon.com/s?k=headphones"
    ]
    
    scraper.scrape_products(category_urls, max_products=200)

if __name__ == "__main__":
    main() 