"""
FastAPI routes for the enhanced scraper service.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import asyncio

from app.schemas import ScrapeRequest, ScrapeResponse, ArticleSearchRequest, ArticleSearchResponse
from app.pipeline import Pipeline

router = APIRouter()


async def get_pipeline() -> Pipeline:
    """
    Dependency to get a pipeline instance.
    
    Returns:
        Pipeline: An instance of the Pipeline class
    """
    pipeline = Pipeline()
    try:
        yield pipeline
    finally:
        await pipeline.close()


@router.post("/scrape", response_model=ScrapeResponse, summary="Scrape and enrich articles from URLs")
async def scrape_urls(request: ScrapeRequest, pipeline: Pipeline = Depends(get_pipeline)):
    """
    Scrape and enrich articles from a list of URLs.
    
    This endpoint accepts a list of URLs and returns all articles found on those pages,
    enriched with NLP features, fake news detection, and stored in MongoDB.
    
    Args:
        request: ScrapeRequest containing a list of URLs to scrape
        pipeline: Pipeline instance (injected by dependency)
        
    Returns:
        ScrapeResponse: Object containing scraped and enriched articles and any errors
        
    Raises:
        HTTPException: If no valid URLs are provided
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    # Convert URLs to strings
    urls = [str(url) for url in request.urls]
    
    # Process URLs through the pipeline
    articles, errors = await pipeline.process_urls(urls)
    
    # Return response
    return ScrapeResponse(
        articles=articles,
        errors=errors
    )


@router.get("/articles", response_model=ArticleSearchResponse, summary="Search for articles in the database")
async def search_articles(
    q: str = Query(..., description="Search query string"),
    limit: int = Query(10, description="Maximum number of results to return"),
    skip: int = Query(0, description="Number of results to skip (for pagination)"),
    pipeline: Pipeline = Depends(get_pipeline)
):
    """
    Search for articles in the database.
    
    This endpoint allows searching for articles in the MongoDB database
    using a text search query.
    
    Args:
        q: Search query string
        limit: Maximum number of results to return
        skip: Number of results to skip (for pagination)
        pipeline: Pipeline instance (injected by dependency)
        
    Returns:
        ArticleSearchResponse: Object containing search results and pagination info
        
    Raises:
        HTTPException: If the search query is empty
    """
    if not q:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    # Search for articles
    results = await pipeline.search_articles(q, limit, skip)
    
    # Return response
    return ArticleSearchResponse(
        articles=results["articles"],
        total=results["total"],
        page=results["page"],
        total_pages=results["total_pages"]
    )


@router.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Status of the service
    """
    return {"status": "ok", "version": "2.0.0"}
