from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ScrapeRequest(BaseModel):
    """
    Request model for the scrape endpoint.
    
    Attributes:
        urls: List of URLs to scrape for articles
    """
    urls: List[HttpUrl] = Field(..., description="List of URLs to scrape for articles")


class Article(BaseModel):
    """
    Model representing a scraped and enriched article.
    
    Attributes:
        title: The title of the article
        content: The full cleaned text content of the article
        summary: AI-generated summary of the article
        keywords: List of extracted keywords from the article
        image_urls: List of image URLs found in the article
        logo_url: URL of the website logo
        publication_date: The publication date of the article (if available)
        scraped_at: Timestamp when the article was scraped
        language: The detected language of the article content
        url: The URL of the article
        source_domain: The domain of the article source
        is_fake_news: Whether the article is classified as fake news
        confidence_score: Confidence score of the fake news classification
    """
    title: str = Field(..., description="The title of the article")
    content: str = Field(..., description="The full cleaned text content of the article")
    summary: Optional[str] = Field(None, description="AI-generated summary of the article")
    keywords: List[str] = Field(default_factory=list, description="List of extracted keywords from the article")
    image_urls: List[str] = Field(default_factory=list, description="List of image URLs found in the article")
    logo_url: Optional[str] = Field(None, description="URL of the website logo")
    publication_date: Optional[str] = Field(None, description="The publication date of the article (if available)")
    scraped_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp when the article was scraped")
    language: str = Field(..., description="The detected language of the article content")
    url: HttpUrl = Field(..., description="The URL of the article")
    source_domain: str = Field(..., description="The domain of the article source")
    is_fake_news: Optional[bool] = Field(None, description="Whether the article is classified as fake news")
    confidence_score: Optional[float] = Field(None, description="Confidence score of the fake news classification")


class ScrapeResponse(BaseModel):
    """
    Response model for the scrape endpoint.
    
    Attributes:
        articles: List of scraped and enriched articles
        errors: List of URLs that could not be scraped with error messages
    """
    articles: List[Article] = Field(default_factory=list, description="List of scraped and enriched articles")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of URLs that could not be scraped with error messages")


class ArticleSearchRequest(BaseModel):
    """
    Request model for searching articles in the database.
    
    Attributes:
        query: Search query string
        limit: Maximum number of results to return
        skip: Number of results to skip (for pagination)
    """
    query: str = Field(..., description="Search query string")
    limit: int = Field(10, description="Maximum number of results to return")
    skip: int = Field(0, description="Number of results to skip (for pagination)")


class ArticleSearchResponse(BaseModel):
    """
    Response model for the article search endpoint.
    
    Attributes:
        articles: List of articles matching the search query
        total: Total number of matching articles
        page: Current page number
        total_pages: Total number of pages
    """
    articles: List[Article] = Field(default_factory=list, description="List of articles matching the search query")
    total: int = Field(0, description="Total number of matching articles")
    page: int = Field(1, description="Current page number")
    total_pages: int = Field(1, description="Total number of pages")
