"""
URL cleaning utilities for normalizing image and logo URLs.
"""
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode
from typing import Optional, List
from loguru import logger


def normalize_url(url: str) -> Optional[str]:
    """
    Normalize a URL by removing tracking parameters, fragments, etc.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL or None if invalid
    """
    if not url:
        return None
    
    try:
        # Parse URL
        parsed = urlparse(url)
        
        # Check if URL is valid
        if not parsed.netloc:
            return None
        
        # Get query parameters
        query_params = parse_qs(parsed.query)
        
        # Remove common tracking parameters
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', 'ref', 'source', 'referrer', 'mc_cid', 'mc_eid'
        ]
        
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
        logger.error(f"Error normalizing URL {url}: {str(e)}")
        return url


def normalize_image_url(image_url: str, base_url: str) -> Optional[str]:
    """
    Normalize an image URL, converting relative URLs to absolute.
    
    Args:
        image_url: Image URL to normalize
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Normalized image URL or None if invalid
    """
    if not image_url:
        return None
    
    try:
        # Check if URL is relative
        parsed = urlparse(image_url)
        if not parsed.netloc:
            # Convert relative URL to absolute
            absolute_url = urljoin(base_url, image_url)
            return normalize_url(absolute_url)
        
        # Already absolute, just normalize
        return normalize_url(image_url)
    
    except Exception as e:
        logger.error(f"Error normalizing image URL {image_url}: {str(e)}")
        return image_url


def normalize_image_urls(image_urls: List[str], base_url: str) -> List[str]:
    """
    Normalize a list of image URLs.
    
    Args:
        image_urls: List of image URLs to normalize
        base_url: Base URL for resolving relative URLs
        
    Returns:
        List of normalized image URLs
    """
    normalized = []
    
    for url in image_urls:
        norm_url = normalize_image_url(url, base_url)
        if norm_url:
            normalized.append(norm_url)
    
    # Remove duplicates while preserving order
    seen = set()
    return [url for url in normalized if not (url in seen or seen.add(url))]


def extract_domain(url: str) -> Optional[str]:
    """
    Extract the domain from a URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain or None if invalid
    """
    if not url:
        return None
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    
    except Exception as e:
        logger.error(f"Error extracting domain from URL {url}: {str(e)}")
        return None
