"""
Helper utilities for the enhanced scraper service.
"""
import os
import sys
from loguru import logger
from typing import Dict, Any, Optional


def setup_logger():
    """
    Configure the logger with appropriate settings.
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logger
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )
    
    # Add file handler for errors
    logger.add(
        os.path.join(logs_dir, "errors.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention="1 week"
    )
    
    # Add file handler for all logs
    logger.add(
        os.path.join(logs_dir, "all.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="3 days"
    )
    
    logger.info("Logger configured")


def clean_html(html_content: str) -> str:
    """
    Clean HTML content by removing scripts, styles, and other unwanted elements.
    
    Args:
        html_content: HTML content to clean
        
    Returns:
        Cleaned HTML content
    """
    try:
        from bs4 import BeautifulSoup
        
        # Parse HTML
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove scripts, styles, and other unwanted elements
        for element in soup(["script", "style", "iframe", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        # Return cleaned HTML
        return str(soup)
    
    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        return html_content


def extract_text_from_html(html_content: str) -> str:
    """
    Extract text from HTML content.
    
    Args:
        html_content: HTML content to extract text from
        
    Returns:
        Extracted text
    """
    try:
        from bs4 import BeautifulSoup
        
        # Parse HTML
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract text
        text = soup.get_text(separator="\n\n")
        
        # Clean text
        text = clean_text(text)
        
        return text
    
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {str(e)}")
        return ""


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace, normalizing line breaks, etc.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    import re
    
    # Replace multiple newlines with a single newline
    text = re.sub(r"\n+", "\n", text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r" +", " ", text)
    
    # Remove leading and trailing whitespace
    text = text.strip()
    
    return text


def format_error(error: Exception, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Format an error for API response.
    
    Args:
        error: Exception to format
        url: URL that caused the error
        
    Returns:
        Formatted error dictionary
    """
    import traceback
    
    return {
        "url": url or "Unknown URL",
        "error": str(error),
        "traceback": traceback.format_exc()
    }
