"""
Enhanced core scraper module with support for extracting images and logos.
"""
import asyncio
import traceback
from typing import List, Dict, Any, Tuple, Optional
from urllib.parse import urlparse
import newspaper
from newspaper import Article as NewspaperArticle
from newspaper.article import ArticleException
from goose3 import Goose
from trafilatura import fetch_url, extract
from readability import Document
from bs4 import BeautifulSoup
import langdetect
import langid
from loguru import logger
from playwright.async_api import async_playwright

from app.utils.url_cleaners.normalizer import normalize_url, extract_domain


class Scraper:
    """
    Enhanced scraper with multiple fallback mechanisms and support for extracting images and logos.
    """
    
    def __init__(self):
        """Initialize the scraper with necessary components."""
        logger.info("Initializing enhanced scraper")
        self.playwright = None
        self.browser = None
    
    async def scrape_urls(self, urls: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scrape articles from a list of URLs.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Tuple of (articles, errors)
        """
        articles = []
        errors = []
        
        # Initialize playwright browser if not already initialized
        if not self.browser:
            await self._init_browser()
        
        # Process URLs concurrently
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                # Handle exception
                logger.error(f"Error scraping {url}: {str(result)}")
                errors.append({
                    "url": url,
                    "error": f"Error: {str(result)}",
                    "traceback": traceback.format_exc()
                })
            elif isinstance(result, tuple) and len(result) == 2:
                # Unpack result
                url_articles, url_errors = result
                
                # Add articles
                articles.extend(url_articles)
                
                # Add errors
                errors.extend(url_errors)
            else:
                # Unexpected result
                logger.error(f"Unexpected result for {url}: {result}")
                errors.append({
                    "url": url,
                    "error": f"Unexpected result: {result}",
                    "traceback": None
                })
        
        return articles, errors
    
    async def scrape_url(self, url: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scrape articles from a single URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (articles, errors)
        """
        articles = []
        errors = []
        
        try:
            # Normalize URL
            normalized_url = normalize_url(url)
            if not normalized_url:
                raise ValueError(f"Invalid URL: {url}")
            
            # Try to build a newspaper source to check if it's a listing page
            source = newspaper.build(normalized_url, memoize_articles=False)
            
            if len(source.articles) > 1:
                # It's a listing page, scrape all articles
                logger.info(f"Found {len(source.articles)} articles on {normalized_url}")
                
                # Process articles concurrently
                tasks = [self._scrape_article(article.url, normalized_url) for article in source.articles[:10]]  # Limit to 10 articles
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for article_url, result in zip([a.url for a in source.articles[:10]], results):
                    if isinstance(result, Exception):
                        # Handle exception
                        logger.error(f"Error scraping article {article_url}: {str(result)}")
                        errors.append({
                            "url": article_url,
                            "error": f"Error: {str(result)}",
                            "traceback": traceback.format_exc()
                        })
                    elif result:
                        # Add article
                        articles.append(result)
            else:
                # It's a single article, scrape it
                article = await self._scrape_article(normalized_url)
                if article:
                    articles.append(article)
        
        except Exception as e:
            # Handle exception
            logger.error(f"Error scraping {url}: {str(e)}")
            errors.append({
                "url": url,
                "error": f"Error: {str(e)}",
                "traceback": traceback.format_exc()
            })
        
        return articles, errors
    
    async def _scrape_article(self, url: str, base_url: str = None) -> Optional[Dict[str, Any]]:
        """
        Scrape a single article using multiple fallback mechanisms.
        
        Args:
            url: URL of the article to scrape
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Article data or None if scraping fails
        """
        # Use base_url if provided, otherwise use the article URL
        base_url = base_url or url
        
        # Try different scraping methods
        methods = [
            self._scrape_with_newspaper,
            self._scrape_with_trafilatura,
            self._scrape_with_goose,
            self._scrape_with_readability,
            self._scrape_with_playwright
        ]
        
        for method in methods:
            try:
                article = await method(url)
                if article and article.get("content"):
                    # Add source domain
                    article["source_domain"] = extract_domain(url)
                    
                    # Extract logo if not already present
                    if not article.get("logo_url"):
                        article["logo_url"] = await self._extract_logo(url)
                    
                    return article
            except Exception as e:
                logger.warning(f"Method {method.__name__} failed for {url}: {str(e)}")
        
        # All methods failed
        logger.error(f"All scraping methods failed for {url}")
        return None
    
    async def _scrape_with_newspaper(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape an article using newspaper3k.
        
        Args:
            url: URL of the article to scrape
            
        Returns:
            Article data or None if scraping fails
        """
        try:
            # Download and parse article
            article = NewspaperArticle(url)
            article.download()
            article.parse()
            
            # Extract data
            data = {
                "title": article.title,
                "content": article.text,
                "url": url,
                "language": article.meta_lang or self._detect_language(article.text),
                "publication_date": article.publish_date.isoformat() if article.publish_date else None,
                "image_urls": [article.top_image] if article.top_image else []
            }
            
            # Add all images
            if article.images:
                data["image_urls"] = list(article.images)
            
            return data
        
        except Exception as e:
            logger.warning(f"Newspaper scraping failed for {url}: {str(e)}")
            return None
    
    async def _scrape_with_trafilatura(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape an article using trafilatura.
        
        Args:
            url: URL of the article to scrape
            
        Returns:
            Article data or None if scraping fails
        """
        try:
            # Fetch and extract content
            downloaded = fetch_url(url)
            if not downloaded:
                return None
            
            result = extract(downloaded, include_images=True, include_links=False, output_format="json")
            if not result:
                return None
            
            import json
            result_dict = json.loads(result)
            
            # Extract data
            data = {
                "title": result_dict.get("title", ""),
                "content": result_dict.get("text", ""),
                "url": url,
                "language": result_dict.get("language") or self._detect_language(result_dict.get("text", "")),
                "publication_date": result_dict.get("date"),
                "image_urls": []
            }
            
            # Extract images
            if "images" in result_dict and result_dict["images"]:
                data["image_urls"] = result_dict["images"]
            
            return data
        
        except Exception as e:
            logger.warning(f"Trafilatura scraping failed for {url}: {str(e)}")
            return None
    
    async def _scrape_with_goose(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape an article using goose3.
        
        Args:
            url: URL of the article to scrape
            
        Returns:
            Article data or None if scraping fails
        """
        try:
            # Extract article
            with Goose() as g:
                article = g.extract(url=url)
            
            # Extract data
            data = {
                "title": article.title,
                "content": article.cleaned_text,
                "url": url,
                "language": article.meta_lang or self._detect_language(article.cleaned_text),
                "publication_date": article.publish_date,
                "image_urls": [article.top_image.src] if article.top_image else []
            }
            
            # Add all images
            if article.images:
                data["image_urls"] = [img.src for img in article.images]
            
            return data
        
        except Exception as e:
            logger.warning(f"Goose scraping failed for {url}: {str(e)}")
            return None
    
    async def _scrape_with_readability(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape an article using readability-lxml.
        
        Args:
            url: URL of the article to scrape
            
        Returns:
            Article data or None if scraping fails
        """
        try:
            # Fetch content
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
            
            # Parse with readability
            doc = Document(html)
            
            # Extract content
            title = doc.title()
            content = doc.summary()
            
            # Clean content with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            text = soup.get_text(separator="\n\n")
            
            # Extract images
            image_urls = []
            for img in soup.find_all("img"):
                if img.get("src"):
                    image_urls.append(img["src"])
            
            # Extract data
            data = {
                "title": title,
                "content": text,
                "url": url,
                "language": self._detect_language(text),
                "publication_date": None,  # Readability doesn't extract publication date
                "image_urls": image_urls
            }
            
            return data
        
        except Exception as e:
            logger.warning(f"Readability scraping failed for {url}: {str(e)}")
            return None
    
    async def _scrape_with_playwright(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape an article using playwright for JavaScript-rendered websites.
        
        Args:
            url: URL of the article to scrape
            
        Returns:
            Article data or None if scraping fails
        """
        try:
            # Initialize browser if not already initialized
            if not self.browser:
                await self._init_browser()
            
            # Create a new page
            page = await self.browser.new_page()
            
            try:
                # Navigate to URL
                await page.goto(url, wait_until="networkidle")
                
                # Extract content
                title = await page.title()
                
                # Extract text content
                content = await page.evaluate("""
                    () => {
                        // Try to find article content
                        const selectors = [
                            'article',
                            '[role="article"]',
                            '.post-content',
                            '.article-content',
                            '.entry-content',
                            '.content',
                            'main'
                        ];
                        
                        for (const selector of selectors) {
                            const element = document.querySelector(selector);
                            if (element) {
                                return element.innerText;
                            }
                        }
                        
                        // Fallback to body content
                        return document.body.innerText;
                    }
                """)
                
                # Extract images
                image_urls = await page.evaluate("""
                    () => {
                        const images = Array.from(document.querySelectorAll('img'));
                        return images
                            .filter(img => img.src && img.width > 100 && img.height > 100)
                            .map(img => img.src);
                    }
                """)
                
                # Extract publication date
                publication_date = await page.evaluate("""
                    () => {
                        // Try to find publication date in meta tags
                        const metaSelectors = [
                            'meta[property="article:published_time"]',
                            'meta[name="publication_date"]',
                            'meta[name="date"]',
                            'meta[name="pubdate"]'
                        ];
                        
                        for (const selector of metaSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.content) {
                                return element.content;
                            }
                        }
                        
                        // Try to find publication date in time elements
                        const timeElements = Array.from(document.querySelectorAll('time'));
                        for (const time of timeElements) {
                            if (time.dateTime) {
                                return time.dateTime;
                            }
                        }
                        
                        return null;
                    }
                """)
                
                # Extract logo
                logo_url = await page.evaluate("""
                    () => {
                        // Try to find logo in link tags
                        const linkSelectors = [
                            'link[rel="icon"]',
                            'link[rel="shortcut icon"]',
                            'link[rel="apple-touch-icon"]'
                        ];
                        
                        for (const selector of linkSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.href) {
                                return element.href;
                            }
                        }
                        
                        // Try to find logo in meta tags
                        const metaSelectors = [
                            'meta[property="og:image"]',
                            'meta[name="twitter:image"]'
                        ];
                        
                        for (const selector of metaSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.content) {
                                return element.content;
                            }
                        }
                        
                        return null;
                    }
                """)
                
                # Extract data
                data = {
                    "title": title,
                    "content": content,
                    "url": url,
                    "language": self._detect_language(content),
                    "publication_date": publication_date,
                    "image_urls": image_urls,
                    "logo_url": logo_url
                }
                
                return data
                
            finally:
                # Close the page
                await page.close()
        
        except Exception as e:
            logger.warning(f"Playwright scraping failed for {url}: {str(e)}")
            return None
    
    async def _extract_logo(self, url: str) -> Optional[str]:
        """
        Extract website logo from a URL.
        
        Args:
            url: URL to extract logo from
            
        Returns:
            Logo URL or None if extraction fails
        """
        try:
            # Parse URL to get domain
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Try to get favicon
            favicon_url = f"{base_url}/favicon.ico"
            
            # Check if favicon exists
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.head(favicon_url) as response:
                    if response.status == 200:
                        return favicon_url
            
            # If favicon doesn't exist, try to extract from HTML
            if self.browser:
                page = await self.browser.new_page()
                try:
                    await page.goto(base_url, wait_until="domcontentloaded")
                    
                    # Extract logo
                    logo_url = await page.evaluate("""
                        () => {
                            // Try to find logo in link tags
                            const linkSelectors = [
                                'link[rel="icon"]',
                                'link[rel="shortcut icon"]',
                                'link[rel="apple-touch-icon"]'
                            ];
                            
                            for (const selector of linkSelectors) {
                                const element = document.querySelector(selector);
                                if (element && element.href) {
                                    return element.href;
                                }
                            }
                            
                            // Try to find logo in meta tags
                            const metaSelectors = [
                                'meta[property="og:image"]',
                                'meta[name="twitter:image"]'
                            ];
                            
                            for (const selector of metaSelectors) {
                                const element = document.querySelector(selector);
                                if (element && element.content) {
                                    return element.content;
                                }
                            }
                            
                            return null;
                        }
                    """)
                    
                    return logo_url
                    
                finally:
                    await page.close()
            
            return None
            
        except Exception as e:
            logger.warning(f"Logo extraction failed for {url}: {str(e)}")
            return None
    
    def _detect_language(self, text: str) -> str:
        """
        Detect the language of a text using multiple libraries.
        
        Args:
            text: Text to detect language for
            
        Returns:
            Language code (ISO 639-1)
        """
        if not text:
            return "en"  # Default to English
        
        try:
            # Try langdetect first
            return langdetect.detect(text)
        except:
            try:
                # Fallback to langid
                lang, _ = langid.classify(text)
                return lang
            except:
                # Default to English
                return "en"
    
    async def _init_browser(self):
        """Initialize the playwright browser."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            logger.info("Playwright browser initialized")
        except Exception as e:
            logger.error(f"Error initializing playwright browser: {str(e)}")
            raise
    
    async def close(self):
        """Close the playwright browser."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
