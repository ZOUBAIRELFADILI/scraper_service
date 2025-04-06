"""
MongoDB integration for storing and retrieving articles.
"""
import motor.motor_asyncio
from pymongo import ReturnDocument
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
from loguru import logger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection string
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://zoubair:Zoubair@123@cluster0.juwfdie.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "scraper_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "articles")


class MongoDBClient:
    """
    MongoDB client for storing and retrieving articles.
    """
    
    def __init__(self, uri: str = MONGODB_URI, db_name: str = DB_NAME, collection_name: str = COLLECTION_NAME):
        """
        Initialize the MongoDB client.
        
        Args:
            uri: MongoDB connection URI
            db_name: Database name
            collection_name: Collection name
        """
        logger.info(f"Initializing MongoDB client with database: {db_name}, collection: {collection_name}")
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
    
    async def store_article(self, article: Dict[str, Any]) -> str:
        """
        Store an article in MongoDB.
        
        Args:
            article: Article to store
            
        Returns:
            ID of the stored article
        """
        if not article.get("url"):
            logger.error("Cannot store article without URL")
            return None
        
        try:
            # Generate a unique ID based on the URL
            article_id = self._generate_id(article["url"])
            
            # Add scraped_at timestamp if not present
            if "scraped_at" not in article:
                article["scraped_at"] = datetime.utcnow().isoformat()
            
            # Convert publication_date to ISO format if it's a datetime object
            if isinstance(article.get("publication_date"), datetime):
                article["publication_date"] = article["publication_date"].isoformat()
            
            # Set _id field to avoid duplicates
            article["_id"] = article_id
            
            # Insert or update the article
            result = await self.collection.find_one_and_update(
                {"_id": article_id},
                {"$set": article},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            
            logger.info(f"Stored article with ID: {article_id}")
            return article_id
            
        except Exception as e:
            logger.error(f"Error storing article: {str(e)}")
            return None
    
    async def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an article by ID.
        
        Args:
            article_id: ID of the article to get
            
        Returns:
            Article document or None if not found
        """
        try:
            article = await self.collection.find_one({"_id": article_id})
            return article
        except Exception as e:
            logger.error(f"Error getting article {article_id}: {str(e)}")
            return None
    
    async def get_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get an article by URL.
        
        Args:
            url: URL of the article to get
            
        Returns:
            Article document or None if not found
        """
        try:
            article_id = self._generate_id(url)
            return await self.get_article(article_id)
        except Exception as e:
            logger.error(f"Error getting article by URL {url}: {str(e)}")
            return None
    
    async def search_articles(self, query: str, limit: int = 10, skip: int = 0) -> Dict[str, Any]:
        """
        Search for articles matching the query.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            
        Returns:
            Dictionary with articles, total count, and pagination info
        """
        try:
            # Create text search query
            search_query = {"$text": {"$search": query}}
            
            # Get total count
            total = await self.collection.count_documents(search_query)
            
            # Get paginated results
            cursor = self.collection.find(search_query).skip(skip).limit(limit)
            articles = await cursor.to_list(length=limit)
            
            # Calculate pagination info
            page = (skip // limit) + 1 if limit > 0 else 1
            total_pages = (total // limit) + (1 if total % limit > 0 else 0) if limit > 0 else 1
            
            return {
                "articles": articles,
                "total": total,
                "page": page,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"Error searching articles: {str(e)}")
            return {
                "articles": [],
                "total": 0,
                "page": 1,
                "total_pages": 1
            }
    
    async def get_recent_articles(self, days: int = 180, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get articles published within the specified number of days.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of articles to return
            
        Returns:
            List of recent articles
        """
        try:
            # Calculate cutoff date
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Query for recent articles
            cursor = self.collection.find(
                {"publication_date": {"$gte": cutoff_date}}
            ).sort("publication_date", -1).limit(limit)
            
            articles = await cursor.to_list(length=limit)
            return articles
            
        except Exception as e:
            logger.error(f"Error getting recent articles: {str(e)}")
            return []
    
    async def setup_indexes(self):
        """Set up necessary indexes for efficient querying."""
        try:
            # Create text index for search
            await self.collection.create_index([
                ("title", "text"),
                ("content", "text"),
                ("summary", "text"),
                ("keywords", "text")
            ])
            
            # Create index on publication_date for date filtering
            await self.collection.create_index("publication_date")
            
            # Create index on source_domain for domain filtering
            await self.collection.create_index("source_domain")
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error setting up MongoDB indexes: {str(e)}")
    
    def _generate_id(self, url: str) -> str:
        """
        Generate a unique ID for an article based on its URL.
        
        Args:
            url: Article URL
            
        Returns:
            Unique ID string
        """
        # Create a hash of the URL
        return hashlib.md5(url.encode()).hexdigest()
