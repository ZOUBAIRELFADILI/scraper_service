from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class ScrapeRequest(BaseModel):
    """
    Request model for the scrape endpoint.
    
    Attributes:
        urls: List of URLs to scrape for articles
    """
    urls: List[HttpUrl] = Field(..., description="List of URLs to scrape for articles")


class Article(BaseModel):
    """
    Model representing a scraped article.
    
    Attributes:
        title: The title of the article
        content: The full cleaned text content of the article
        publication_date: The publication date of the article (if available)
        url: The URL of the article
        language: The detected language of the article content
    """
    title: str = Field(..., description="The title of the article")
    content: str = Field(..., description="The full cleaned text content of the article")
    publication_date: Optional[str] = Field(None, description="The publication date of the article (if available)")
    url: HttpUrl = Field(..., description="The URL of the article")
    language: str = Field(..., description="The detected language of the article content")


class ScrapeResponse(BaseModel):
    """
    Response model for the scrape endpoint.
    
    Attributes:
        articles: List of scraped articles
        errors: List of URLs that could not be scraped with error messages
    """
    articles: List[Article] = Field(default_factory=list, description="List of scraped articles")
    errors: List[dict] = Field(default_factory=list, description="List of URLs that could not be scraped with error messages")
