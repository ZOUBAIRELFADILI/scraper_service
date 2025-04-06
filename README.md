# AI-Powered Content Intelligence Service

A complete FastAPI microservice for scraping, enriching, and analyzing articles from websites with AI capabilities.

## Features

- **Advanced Web Scraping**: Extract articles from any website with multiple fallback mechanisms
- **NLP Enrichment**: Generate summaries and extract keywords using transformer models
- **Fake News Detection**: Classify articles using a transformer-based fake news detector
- **Date Filtering**: Only keep articles published within the last 6 months
- **Image & Logo Extraction**: Extract images and website logos from articles
- **MongoDB Integration**: Store articles with proper schema and deduplication
- **Search Capabilities**: Search stored articles by content, title, or keywords
- **Responsive API**: Clean, well-documented API with proper error handling
- **CORS Support**: Ready for cross-origin requests
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Architecture

```
scraper_service/
├── app/
│   ├── core/
│   │   └── scraper.py         # Enhanced scraper with image extraction
│   ├── db/
│   │   └── mongodb.py         # MongoDB client for storing articles
│   ├── fakenews/
│   │   └── detector.py        # Fake news detection using transformers
│   ├── models/
│   │   └── schemas.py         # Pydantic models for requests/responses
│   ├── nlp/
│   │   └── enrichment.py      # NLP enrichment (summarization, keywords)
│   ├── routers/
│   │   └── scraper.py         # API routes for scraping and searching
│   ├── utils/
│   │   ├── date_filters/      # Date filtering utilities
│   │   ├── url_cleaners/      # URL normalization utilities
│   │   └── helpers.py         # General helper functions
│   ├── main.py                # FastAPI app configuration
│   └── pipeline.py            # Orchestrates the entire workflow
├── tests/
│   ├── test_api.py            # API endpoint tests
│   ├── test_scraper.py        # Core scraper tests
│   └── test_enhanced_service.py # Tests for AI features
├── run.py                     # Service entry point
├── requirements.txt           # Dependencies
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Container orchestration
└── .env                       # Environment variables (not in repo)
```

## API Endpoints

### POST /scrape

Scrape and enrich articles from a list of URLs.

**Request:**
```json
{
  "urls": [
    "https://techcrunch.com",
    "https://medium.com/topic/ai",
    "https://nytimes.com"
  ]
}
```

**Response:**
```json
{
  "articles": [
    {
      "title": "Article Title",
      "content": "Full cleaned text content",
      "summary": "AI-generated summary",
      "keywords": ["ai", "scraping", "nlp"],
      "image_urls": ["https://example.com/image1.jpg"],
      "logo_url": "https://example.com/logo.png",
      "publication_date": "2024-11-05T10:30:00",
      "scraped_at": "2024-04-06T14:12:00",
      "language": "en",
      "url": "https://example.com/article-url",
      "source_domain": "example.com",
      "is_fake_news": false,
      "confidence_score": 0.91
    }
  ],
  "errors": [
    {
      "url": "https://invalid-url.com",
      "error": "Error description",
      "traceback": "Error traceback"
    }
  ]
}
```

### GET /articles

Search for articles in the database.

**Parameters:**
- `q` (required): Search query string
- `limit` (optional): Maximum number of results to return (default: 10)
- `skip` (optional): Number of results to skip for pagination (default: 0)

**Response:**
```json
{
  "articles": [
    {
      "title": "Article Title",
      "content": "Full cleaned text content",
      "summary": "AI-generated summary",
      "keywords": ["ai", "scraping", "nlp"],
      "image_urls": ["https://example.com/image1.jpg"],
      "logo_url": "https://example.com/logo.png",
      "publication_date": "2024-11-05T10:30:00",
      "scraped_at": "2024-04-06T14:12:00",
      "language": "en",
      "url": "https://example.com/article-url",
      "source_domain": "example.com",
      "is_fake_news": false,
      "confidence_score": 0.91
    }
  ],
  "total": 42,
  "page": 1,
  "total_pages": 5
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "version": "2.0.0"
}
```

## Installation

### Prerequisites

- Python 3.10+
- MongoDB database
- Sufficient disk space for AI models (at least 5GB recommended)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ZOUBAIRELFADILI/scraper_service.git
cd scraper_service
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

5. Create a `.env` file with your MongoDB connection string:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=scraper_db
COLLECTION_NAME=articles
```

6. Run the service:
```bash
python run.py
```

The service will be available at http://localhost:8000.

## Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```

2. The service will be available at http://localhost:8000.

## System Requirements

- **CPU**: 4+ cores recommended for parallel scraping
- **RAM**: 8GB+ (16GB+ recommended for large transformer models)
- **Disk**: 5GB+ for AI models and dependencies
- **Network**: Stable internet connection for scraping and API access

## Development

### Running Tests

```bash
pytest tests/
```

### API Documentation

When the service is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT

## Acknowledgements

This project uses several open-source libraries:
- FastAPI for the API framework
- Newspaper3k, Trafilatura, and Goose3 for article extraction
- Transformers and PyTorch for NLP models
- Motor and PyMongo for MongoDB integration
- Playwright for JavaScript-rendered websites
