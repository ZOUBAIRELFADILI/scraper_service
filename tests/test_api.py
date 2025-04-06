from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Scraper Service"
    assert response.json()["version"] == "1.0.0"
    assert response.json()["documentation"] == "/docs"

def test_scrape_empty_urls():
    """Test scraping with empty URLs list."""
    response = client.post("/scrape", json={"urls": []})
    assert response.status_code == 400
    assert "No URLs provided" in response.json()["detail"]

# This test requires internet connection and might be flaky depending on the website
def test_scrape_single_url():
    """Test scraping a single URL."""
    # Using a stable test website
    response = client.post("/scrape", json={"urls": ["https://example.com"]})
    assert response.status_code == 200
    assert "articles" in response.json()
    assert "errors" in response.json()
    # example.com has a simple page with a title "Example Domain"
    if response.json()["articles"]:
        assert "Example Domain" in response.json()["articles"][0]["title"]
