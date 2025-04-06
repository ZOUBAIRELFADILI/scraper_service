import re
from typing import Optional
from bs4 import BeautifulSoup
from loguru import logger


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace, special characters, and normalizing line breaks.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def clean_html(html: str) -> str:
    """
    Clean HTML by removing unwanted elements like ads, scripts, and navigation.
    
    Args:
        html: HTML content to clean
        
    Returns:
        Cleaned HTML
    """
    if not html:
        return ""
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 
                                     'aside', 'iframe', 'noscript', 'svg', 'form',
                                     'button', 'input', 'textarea', 'select']):
            element.decompose()
        
        # Remove elements with common ad class names
        ad_classes = ['ad', 'ads', 'advertisement', 'banner', 'sponsored', 'social',
                     'share', 'related', 'recommended', 'newsletter', 'popup', 'modal']
        
        for class_name in ad_classes:
            for element in soup.find_all(class_=lambda c: c and class_name in c.lower()):
                element.decompose()
        
        # Remove elements with common ad IDs
        ad_ids = ['ad', 'ads', 'advertisement', 'banner', 'sponsored', 'social',
                 'share', 'related', 'recommended', 'newsletter', 'popup', 'modal']
        
        for id_name in ad_ids:
            for element in soup.find_all(id=lambda i: i and id_name in i.lower()):
                element.decompose()
        
        return str(soup)
    except Exception as e:
        logger.error(f"Error cleaning HTML: {str(e)}")
        return html


def extract_main_image_url(html: str, base_url: str) -> Optional[str]:
    """
    Extract the main image URL from HTML content.
    
    Args:
        html: HTML content
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Main image URL or None if not found
    """
    if not html:
        return None
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to find meta og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
        
        # Try to find meta twitter:image
        twitter_image = soup.find('meta', property='twitter:image')
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
        
        # Try to find the first large image
        for img in soup.find_all('img', src=True):
            # Skip small images, icons, etc.
            if img.get('width') and int(img['width']) < 200:
                continue
            if img.get('height') and int(img['height']) < 200:
                continue
            
            # Get image URL
            img_url = img['src']
            
            # Convert relative URL to absolute
            if not img_url.startswith(('http://', 'https://')):
                from urllib.parse import urljoin
                img_url = urljoin(base_url, img_url)
            
            return img_url
        
        return None
    except Exception as e:
        logger.error(f"Error extracting main image URL: {str(e)}")
        return None


def normalize_url(url: str) -> str:
    """
    Normalize URL by removing tracking parameters, fragments, etc.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    if not url:
        return ""
    
    try:
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        
        # Parse URL
        parsed = urlparse(url)
        
        # Get query parameters
        query_params = parse_qs(parsed.query)
        
        # Remove common tracking parameters
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 
                          'utm_content', 'fbclid', 'gclid', 'msclkid', 'ref']
        
        for param in tracking_params:
            if param in query_params:
                del query_params[param]
        
        # Rebuild query string
        query_string = urlencode(query_params, doseq=True)
        
        # Rebuild URL without fragment
        normalized_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query_string,
            ''  # No fragment
        ))
        
        return normalized_url
    except Exception as e:
        logger.error(f"Error normalizing URL: {str(e)}")
        return url


def setup_logger():
    """Configure the logger for the application."""
    import sys
    import os
    from loguru import logger
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file logger
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    logger.add(
        os.path.join(log_dir, "scraper.log"),
        rotation="10 MB",
        retention="1 week",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    return logger
