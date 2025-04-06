"""
Date filtering utilities for articles.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from loguru import logger


def is_recent_article(article: Dict[str, Any], max_age_days: int = 180) -> bool:
    """
    Check if an article is recent (published within the specified number of days).
    
    Args:
        article: Article to check
        max_age_days: Maximum age in days for an article to be considered recent
        
    Returns:
        True if the article is recent, False otherwise
    """
    # Skip if no publication date
    if not article.get("publication_date"):
        logger.debug(f"Article has no publication date: {article.get('url')}")
        return False
    
    try:
        # Parse publication date
        pub_date = parse_date(article["publication_date"])
        if not pub_date:
            return False
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        # Check if article is recent
        return pub_date >= cutoff_date
        
    except Exception as e:
        logger.error(f"Error checking if article is recent: {str(e)}")
        return False


def filter_recent_articles(articles: List[Dict[str, Any]], max_age_days: int = 180) -> List[Dict[str, Any]]:
    """
    Filter a list of articles to only include recent ones.
    
    Args:
        articles: List of articles to filter
        max_age_days: Maximum age in days for an article to be considered recent
        
    Returns:
        List of recent articles
    """
    return [article for article in articles if is_recent_article(article, max_age_days)]


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string into a datetime object.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Try different date formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",  # ISO format with seconds
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with microseconds
        "%Y-%m-%dT%H:%M:%SZ",  # ISO format with Z
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds and Z
        "%Y-%m-%dT%H:%M",  # ISO format without seconds
        "%Y-%m-%d %H:%M:%S",  # Standard format with seconds
        "%Y-%m-%d %H:%M",  # Standard format without seconds
        "%Y-%m-%d",  # Date only
        "%d/%m/%Y",  # European format
        "%m/%d/%Y",  # US format
        "%d-%m-%Y",  # European format with dashes
        "%m-%d-%Y",  # US format with dashes
        "%B %d, %Y",  # Month name, day, year
        "%d %B %Y",  # Day, month name, year
        "%Y/%m/%d",  # Year, month, day with slashes
    ]
    
    # If date_str is already a datetime object, return it
    if isinstance(date_str, datetime):
        return date_str
    
    # Try each format
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # If all formats fail, try to extract a date using regex
    try:
        import re
        # Look for YYYY-MM-DD pattern
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year, month, day = map(int, match.groups())
            return datetime(year, month, day)
    except Exception:
        pass
    
    logger.warning(f"Could not parse date: {date_str}")
    return None
