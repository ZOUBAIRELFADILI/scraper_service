# Scraper Service

A FastAPI microservice for web scraping that extracts articles from various websites with multiple fallback mechanisms for resilience.

## Features

- Scrapes articles from any website URL
- Extracts all articles from listing pages (like news homepages)
- Uses multiple fallback libraries for increased accuracy and resilience:
  - newspaper3k
  - trafilatura
  - goose3
  - readability-lxml
  - BeautifulSoup (as last resort)
- Supports JavaScript-rendered websites using Playwright
- Detects and returns content language
- Cleans text by removing ads, navbars, scripts, and boilerplate
- Handles errors gracefully for unreachable, blocked, or malformed URLs
- Asynchronous architecture for improved performance
- CORS middleware for cross-origin requests
- Comprehensive logging

## Installation

### Prerequisites

- Python 3.10+
- pip

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/scraper-service.git
cd scraper-service
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:

```bash
playwright install chromium
```

## Usage

### Running the Service

Start the service with uvicorn:

```bash
cd scraper-service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at http://localhost:8000

### API Endpoints

#### Health Check

```
GET /health
```

Returns the status of the service.

#### Scrape Articles

```
POST /scrape
```

Request body:

```json
{
  "urls": [
    "https://techcrunch.com",
    "https://medium.com/topic/ai",
    "https://nytimes.com"
  ]
}
```

Response:

```json
{
  "articles": [
    {
      "title": "Article Title",
      "content": "Full cleaned text content",
      "publication_date": "2024-11-05",
      "url": "https://example.com/article-url",
      "language": "en"
    },
    ...
  ],
  "errors": [
    {
      "url": "https://blocked-site.com",
      "error": "Error message",
      "traceback": "Detailed error traceback"
    },
    ...
  ]
}
```

### Example Usage with Python

```python
import requests

# API endpoint
url = "http://localhost:8000/scrape"

# Request payload
payload = {
    "urls": [
        "https://techcrunch.com",
        "https://example.com"
    ]
}

# Send POST request
response = requests.post(url, json=payload)

# Check if request was successful
if response.status_code == 200:
    data = response.json()
    
    # Process articles
    for article in data["articles"]:
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Language: {article['language']}")
        print(f"Publication Date: {article['publication_date']}")
        print(f"Content (first 150 chars): {article['content'][:150]}...")
        print("\n")
    
    # Process errors
    for error in data["errors"]:
        print(f"Error for URL {error['url']}: {error['error']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Example Usage with cURL

```bash
curl -X 'POST' \
  'http://localhost:8000/scrape' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "urls": [
    "https://techcrunch.com",
    "https://example.com"
  ]
}'
```

## Project Structure

```
scraper-service/
├── app/
│   ├── core/
│   │   └── scraper.py         # Core scraping logic
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── routers/
│   │   └── scraper.py         # API routes
│   ├── utils/
│   │   └── helpers.py         # Utility functions
│   └── main.py                # FastAPI app
├── tests/
│   ├── test_api.py            # API tests
│   └── test_scraper.py        # Scraper tests
├── logs/                      # Log files
├── requirements.txt           # Dependencies
└── README.md                  # Documentation
```

## Future Enhancements

- NLP pipeline for summarization and keyword extraction
- Fake news detection using a transformer model
- Article rating or scoring
- Caching mechanism for improved performance
- Rate limiting to prevent abuse
- Authentication for API access
- Docker containerization

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
