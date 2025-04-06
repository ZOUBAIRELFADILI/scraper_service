"""
Pipeline for orchestrating the entire article processing workflow.
"""
from typing import List, Dict, Any, Tuple
import asyncio
from loguru import logger

from app.core.scraper import Scraper
from app.nlp.enrichment import NLPEnricher
from app.fakenews.detector import FakeNewsDetector
from app.db.mongodb import MongoDBClient
from app.utils.date_filters.filters import is_recent_article, filter_recent_articles
from app.utils.url_cleaners.normalizer import normalize_url, normalize_image_urls, extract_domain


class Pipeline:
    """
    Pipeline for orchestrating the entire article processing workflow.
    """
    
    def __init__(self, max_age_days: int = 180, store_in_db: bool = True):
        """
        Initialize the pipeline with all necessary components.
        
        Args:
            max_age_days: Maximum age in days for an article to be considered recent
            store_in_db: Whether to store articles in MongoDB
        """
        logger.info("Initializing article processing pipeline")
        self.scraper = Scraper()
        self.nlp_enricher = NLPEnricher()
        self.fake_news_detector = FakeNewsDetector()
        self.db_client = MongoDBClient() if store_in_db else None
        self.max_age_days = max_age_days
        self.store_in_db = store_in_db
    
    async def process_urls(self, urls: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process a list of URLs through the entire pipeline.
        
        Args:
            urls: List of URLs to process
            
        Returns:
            Tuple of (processed_articles, errors)
        """
        logger.info(f"Processing {len(urls)} URLs")
        
        # Step 1: Scrape articles
        scraped_articles, errors = await self.scraper.scrape_urls(urls)
        logger.info(f"Scraped {len(scraped_articles)} articles with {len(errors)} errors")
        
        # Step 2: Filter recent articles
        if self.max_age_days > 0:
            recent_articles = filter_recent_articles(scraped_articles, self.max_age_days)
            logger.info(f"Filtered to {len(recent_articles)} recent articles (within {self.max_age_days} days)")
        else:
            recent_articles = scraped_articles
        
        # Step 3: Enrich articles with additional data
        enriched_articles = []
        for article in recent_articles:
            try:
                # Add source domain
                if "url" in article and not article.get("source_domain"):
                    article["source_domain"] = extract_domain(article["url"])
                
                # Normalize image URLs if present
                if "image_urls" in article and article["image_urls"] and "url" in article:
                    article["image_urls"] = normalize_image_urls(article["image_urls"], article["url"])
                
                # Normalize logo URL if present
                if "logo_url" in article and article["logo_url"] and "url" in article:
                    article["logo_url"] = normalize_url(article["logo_url"])
                
                # Apply NLP enrichment
                enriched = await self.nlp_enricher.enrich_article(article)
                
                # Apply fake news detection
                enriched = await self.fake_news_detector.enrich_article(enriched)
                
                enriched_articles.append(enriched)
                
            except Exception as e:
                logger.error(f"Error enriching article {article.get('url')}: {str(e)}")
                errors.append({
                    "url": article.get("url", "Unknown URL"),
                    "error": f"Error during enrichment: {str(e)}",
                    "traceback": None
                })
        
        # Step 4: Store articles in MongoDB
        if self.store_in_db and self.db_client and enriched_articles:
            stored_articles = []
            for article in enriched_articles:
                try:
                    article_id = await self.db_client.store_article(article)
                    if article_id:
                        stored_articles.append(article)
                except Exception as e:
                    logger.error(f"Error storing article {article.get('url')} in MongoDB: {str(e)}")
                    errors.append({
                        "url": article.get("url", "Unknown URL"),
                        "error": f"Error storing in MongoDB: {str(e)}",
                        "traceback": None
                    })
            
            logger.info(f"Stored {len(stored_articles)} articles in MongoDB")
        
        return enriched_articles, errors
    
    async def search_articles(self, query: str, limit: int = 10, skip: int = 0) -> Dict[str, Any]:
        """
        Search for articles in the database.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            
        Returns:
            Search results with pagination info
        """
        if not self.db_client:
            logger.warning("Cannot search articles: MongoDB client not initialized")
            return {
                "articles": [],
                "total": 0,
                "page": 1,
                "total_pages": 1
            }
        
        return await self.db_client.search_articles(query, limit, skip)
    
    async def close(self):
        """Close all resources."""
        await self.scraper.close()
