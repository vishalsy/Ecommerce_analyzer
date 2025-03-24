# E-commerce Data Analyzer

A Python-based backend system that scrapes Amazon product data, analyzes it using AI, and provides insights through a REST API.

## Features

- Web scraping of Amazon product data
- REST API for accessing product information
- AI-powered question answering using OpenAI API
- Simple product database with SQLite

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ecommerce_analyzer.git
   cd ecommerce_analyzer
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration :
   ```
   Then edit the `.env` file to add your OpenAI API key:
   ```
   # Required for AI-powered insights
   OPENAI_API_KEY=your_openai_api_key
   ```

5. Initialize the database:
   ```bash
   python3 manage.py makemigrations
   python3 manage.py migrate
   ```

## Project Structure

```
ecommerce_analyzer/
├── api/                  # Django REST API app
│   ├── models.py         # Database models
│   ├── serializers.py    # API serializers
│   ├── views.py          # API views
│   └── urls.py           # API URL routes
├── scraper/              # Web scraping module
│   ├── scraper.py        # Amazon scraper implementation
│   └── import_data.py    # Script to import scraped data
├── ecommerce_project/    # Django project settings
├── data/                 # Directory for scraped data
└── manage.py             # Django management script
```

## Usage

### Running the Server

To start the Django server:

```bash
python3 manage.py runserver
```

The API will be available at http://127.0.0.1:8000/api/

## API Endpoints

### Products Endpoints

- `GET /api/products/` - List all scraped products
- `GET /api/products/{id}/` - Get a single product's details

### Scraper Endpoint

- `POST /api/scrape/` - Trigger the Amazon product scraper
  - Request body format:
    ```json
    {
      "categories": [
        "laptops",
        "headphones"
      ],
      "max_products": 100  // Optional, defaults to 100, max 500
    }
    ```
  - The system will automatically build Amazon search URLs from the categories

### Insights Endpoint

- `POST /api/insights/` - Ask questions about product data
  - Request body format:
    ```json
    {
      "question": "What are the top rated products?",
      "product_id": null  # Optional, specify for questions about a specific product
    }
    ```
  - Response format:
    ```json
    {
      "answer": "AI-generated answer to your question...",
      "status": "success",
      "provider": "openai"
    }
    ```

## Example Questions for Insights API

### General Questions:
```json
{
  "question": "What are the highest rated products in the database?"
}
```

### Product-Specific Questions:
```json
{
  "question": "Summarize this product for me",
  "product_id": 1
}
```

## Using Curl with the API

### Trigger Scraping:
```bash
# Scrape a single category with default settings (100 products)
curl -X POST http://localhost:8000/api/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"categories": ["laptops"]}'

# Scrape multiple categories with a limit
curl -X POST http://localhost:8000/api/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"categories": ["laptops", "gaming keyboards"], "max_products": 50}'

# Categories with multiple words work fine
curl -X POST http://localhost:8000/api/scrape/ \
  -H "Content-Type: application/json" \
  -d '{"categories": ["wireless headphones", "mechanical keyboards"], "max_products": 200}'
```

### Get Insights:
```bash
curl -X POST http://localhost:8000/api/insights/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the best products under $500?"}'
```

### Required API Key

You'll need to sign up for OpenAI and get an API key:

- **OpenAI** - Sign up at https://openai.com/

Add your API key to the `.env` file as shown in the setup instructions above.

## License

MIT License
