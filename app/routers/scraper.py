from fastapi import APIRouter, HTTPException, Depends
from typing import List
import asyncio

from app.models.schemas import ScrapeRequest, ScrapeResponse, Article
from app.core.scraper import Scraper

router = APIRouter()


async def get_scraper() -> Scraper:
    """
    Dependency to get a scraper instance.
    
    Returns:
        Scraper: An instance of the Scraper class
    """
    scraper = Scraper()
    try:
        yield scraper
    finally:
        await scraper.close()


@router.post("/scrape", response_model=ScrapeResponse, summary="Scrape articles from URLs")
async def scrape_urls(request: ScrapeRequest, scraper: Scraper = Depends(get_scraper)):
    """
    Scrape articles from a list of URLs.
    
    This endpoint accepts a list of URLs and returns all articles found on those pages.
    It uses multiple fallback mechanisms to increase accuracy and resilience.
    
    Args:
        request: ScrapeRequest containing a list of URLs to scrape
        scraper: Scraper instance (injected by dependency)
        
    Returns:
        ScrapeResponse: Object containing scraped articles and any errors
        
    Raises:
        HTTPException: If no valid URLs are provided
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    # Convert URLs to strings
    urls = [str(url) for url in request.urls]
    
    # Scrape articles
    articles, errors = await scraper.scrape_urls(urls)
    
    # Return response
    return ScrapeResponse(
        articles=articles,
        errors=errors
    )
