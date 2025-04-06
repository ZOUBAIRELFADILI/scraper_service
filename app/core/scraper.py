# Core scraper module with multiple fallback mechanisms
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import traceback
from urllib.parse import urljoin
import re
from datetime import datetime

# Import scraping libraries
import newspaper
from newspaper import Article as NewspaperArticle
from trafilatura import fetch_url, extract
from goose3 import Goose
from readability import Document
from bs4 import BeautifulSoup
import langdetect
import langid
from loguru import logger
from playwright.async_api import async_playwright

# Import custom models
from app.models.schemas import Article


class Scraper:
    """
    Core scraper class with multiple fallback mechanisms for article extraction.
    """
    
    def __init__(self):
        """Initialize the scraper with necessary configurations."""
        self.goose = Goose()
        
    async def close(self):
        """Close any resources when done."""
        self.goose.close()
    
    async def scrape_urls(self, urls: List[str]) -> Tuple[List[Article], List[Dict[str, Any]]]:
        """
        Scrape articles from a list of URLs.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Tuple containing list of scraped articles and list of errors
        """
        articles = []
        errors = []
        
        # Create tasks for each URL
        tasks = [self.process_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {url}: {str(result)}")
                errors.append({
                    "url": url,
                    "error": str(result),
                    "traceback": traceback.format_exc()
                })
            elif result:
                articles.extend(result)
            else:
                errors.append({
                    "url": url,
                    "error": "No articles found or unable to parse content",
                    "traceback": None
                })
                
        return articles, errors
    
    async def process_url(self, url: str) -> List[Article]:
        """
        Process a single URL to extract articles.
        
        Args:
            url: URL to process
            
        Returns:
            List of extracted articles
        """
        try:
            # First, check if it's a listing page with multiple articles
            articles = await self.extract_articles_from_listing(url)
            if articles:
                return articles
            
            # If not a listing or no articles found, try to extract as a single article
            article = await self.extract_single_article(url)
            return [article] if article else []
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            raise
    
    async def extract_articles_from_listing(self, url: str) -> List[Article]:
        """
        Extract articles from a listing page (e.g., homepage, category page).
        
        Args:
            url: URL of the listing page
            
        Returns:
            List of extracted articles
        """
        articles = []
        
        try:
            # Try newspaper3k first for listing pages
            news_site = newspaper.build(url, memoize_articles=False)
            
            # If no article URLs found, this might not be a listing page
            if len(news_site.article_urls()) == 0:
                return []
                
            # Process each article URL
            article_tasks = []
            for article_url in news_site.article_urls():
                article_tasks.append(self.extract_single_article(article_url))
            
            # Gather results
            article_results = await asyncio.gather(*article_tasks, return_exceptions=True)
            
            # Filter successful results
            for result in article_results:
                if isinstance(result, Article):
                    articles.append(result)
                    
            return articles
            
        except Exception as e:
            logger.warning(f"Failed to extract articles from listing {url} using newspaper3k: {str(e)}")
            
            # Fallback: Try to extract article links using BeautifulSoup
            try:
                html = await self._fetch_html_with_js_rendering(url)
                if not html:
                    return []
                    
                soup = BeautifulSoup(html, 'html.parser')
                article_links = []
                
                # Look for common article link patterns
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    # Convert relative URLs to absolute
                    if not href.startswith(('http://', 'https://')):
                        href = urljoin(url, href)
                    
                    # Check if URL likely points to an article
                    if self._is_likely_article_url(href):
                        article_links.append(href)
                
                # Process each article URL
                article_tasks = []
                for article_url in set(article_links):  # Remove duplicates
                    article_tasks.append(self.extract_single_article(article_url))
                
                # Gather results
                if article_tasks:
                    article_results = await asyncio.gather(*article_tasks, return_exceptions=True)
                    
                    # Filter successful results
                    for result in article_results:
                        if isinstance(result, Article) and not isinstance(result, Exception):
                            articles.append(result)
                
                return articles
                
            except Exception as fallback_e:
                logger.error(f"Fallback extraction also failed for {url}: {str(fallback_e)}")
                return []
    
    async def extract_single_article(self, url: str) -> Optional[Article]:
        """
        Extract a single article from a URL using multiple fallback mechanisms.
        
        Args:
            url: URL of the article
            
        Returns:
            Extracted article or None if extraction failed
        """
        # Try multiple extraction methods in sequence
        article = await self._extract_with_newspaper3k(url)
        
        if not article or not article.content.strip():
            article = await self._extract_with_trafilatura(url)
            
        if not article or not article.content.strip():
            article = await self._extract_with_goose(url)
            
        if not article or not article.content.strip():
            article = await self._extract_with_readability(url)
            
        if not article or not article.content.strip():
            article = await self._extract_with_beautifulsoup(url)
            
        # If all methods failed, return None
        if not article or not article.content.strip():
            return None
            
        # Detect language if not already set
        if not hasattr(article, 'language') or not article.language:
            article.language = self._detect_language(article.content)
            
        return article
    
    async def _extract_with_newspaper3k(self, url: str) -> Optional[Article]:
        """Extract article using newspaper3k library."""
        try:
            news_article = NewspaperArticle(url)
            news_article.download()
            news_article.parse()
            
            # Format publication date if available
            pub_date = None
            if news_article.publish_date:
                pub_date = news_article.publish_date.strftime('%Y-%m-%d')
            
            return Article(
                title=news_article.title,
                content=news_article.text,
                publication_date=pub_date,
                url=url,
                language=news_article.meta_lang or self._detect_language(news_article.text)
            )
        except Exception as e:
            logger.warning(f"newspaper3k extraction failed for {url}: {str(e)}")
            return None
    
    async def _extract_with_trafilatura(self, url: str) -> Optional[Article]:
        """Extract article using trafilatura library."""
        try:
            downloaded = fetch_url(url)
            if not downloaded:
                return None
                
            extracted_text = extract(downloaded, include_comments=False, include_tables=False)
            if not extracted_text:
                return None
                
            # Try to extract title from HTML
            soup = BeautifulSoup(downloaded, 'html.parser')
            title = soup.title.string if soup.title else "Unknown Title"
            
            # Try to find publication date
            pub_date = self._extract_date_from_html(soup)
            
            return Article(
                title=title,
                content=extracted_text,
                publication_date=pub_date,
                url=url,
                language=self._detect_language(extracted_text)
            )
        except Exception as e:
            logger.warning(f"trafilatura extraction failed for {url}: {str(e)}")
            return None
    
    async def _extract_with_goose(self, url: str) -> Optional[Article]:
        """Extract article using goose3 library."""
        try:
            article = self.goose.extract(url=url)
            
            if not article.cleaned_text:
                return None
                
            # Format publication date if available
            pub_date = None
            if article.publish_date:
                pub_date = article.publish_date.strftime('%Y-%m-%d')
                
            return Article(
                title=article.title,
                content=article.cleaned_text,
                publication_date=pub_date,
                url=url,
                language=article.meta_lang or self._detect_language(article.cleaned_text)
            )
        except Exception as e:
            logger.warning(f"goose3 extraction failed for {url}: {str(e)}")
            return None
    
    async def _extract_with_readability(self, url: str) -> Optional[Article]:
        """Extract article using readability-lxml library."""
        try:
            html = await self._fetch_html_with_js_rendering(url)
            if not html:
                return None
                
            doc = Document(html)
            content = doc.summary()
            
            # Clean HTML tags from content
            soup = BeautifulSoup(content, 'html.parser')
            cleaned_text = soup.get_text(separator='\n', strip=True)
            
            # Extract title
            title = doc.title()
            
            # Try to find publication date
            pub_date = self._extract_date_from_html(BeautifulSoup(html, 'html.parser'))
            
            return Article(
                title=title,
                content=cleaned_text,
                publication_date=pub_date,
                url=url,
                language=self._detect_language(cleaned_text)
            )
        except Exception as e:
            logger.warning(f"readability-lxml extraction failed for {url}: {str(e)}")
            return None
    
    async def _extract_with_beautifulsoup(self, url: str) -> Optional[Article]:
        """Extract article using BeautifulSoup as a last resort."""
        try:
            html = await self._fetch_html_with_js_rendering(url)
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Extract title
            title = soup.title.string if soup.title else "Unknown Title"
            
            # Try to find main content
            main_content = None
            for tag in ['article', 'main', '.content', '#content', '.post', '.article']:
                if tag.startswith('.') or tag.startswith('#'):
                    main_content = soup.select_one(tag)
                else:
                    main_content = soup.find(tag)
                    
                if main_content:
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.body
                
            # Extract text
            if main_content:
                content = main_content.get_text(separator='\n', strip=True)
            else:
                content = soup.get_text(separator='\n', strip=True)
                
            # Try to find publication date
            pub_date = self._extract_date_from_html(soup)
            
            # Only return if we have meaningful content
            if len(content) > 100:  # Arbitrary threshold to avoid empty or too short content
                return Article(
                    title=title,
                    content=content,
                    publication_date=pub_date,
                    url=url,
                    language=self._detect_language(content)
                )
            return None
        except Exception as e:
            logger.warning(f"BeautifulSoup extraction failed for {url}: {str(e)}")
            return None
    
    async def _fetch_html_with_js_rendering(self, url: str) -> Optional[str]:
        """
        Fetch HTML content with JavaScript rendering support using Playwright.
        Falls back to simple HTTP request if Playwright fails.
        """
        # First try with Playwright for JS rendering
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set timeout and user agent
                page.set_default_timeout(30000)  # 30 seconds
                await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
                
                # Navigate to the URL
                await page.goto(url, wait_until="networkidle")
                
                # Wait a bit for any lazy-loaded content
                await asyncio.sleep(2)
                
                # Get the HTML content
                content = await page.content()
                
                # Close browser
                await browser.close()
                
                return content
        except Exception as e:
            logger.warning(f"Playwright rendering failed for {url}: {str(e)}, falling back to simple fetch")
            
            # Fallback to simple fetch
            try:
                from urllib.request import Request, urlopen
                
                req = Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                )
                with urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8', errors='replace')
            except Exception as fetch_e:
                logger.error(f"Simple fetch also failed for {url}: {str(fetch_e)}")
                return None
    
    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the text using multiple libraries for reliability.
        
        Args:
            text: Text to detect language for
            
        Returns:
            ISO 639-1 language code (e.g., 'en', 'fr')
        """
        if not text or len(text.strip()) < 10:
            return "unknown"
            
        # Try langdetect first
        try:
            return langdetect.detect(text)
        except Exception:
            # Fallback to langid
            try:
                lang, _ = langid.classify(text)
                return lang
            except Exception:
                return "unknown"
    
    def _extract_date_from_html(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract publication date from HTML using common patterns.
        
        Args:
            soup: BeautifulSoup object of the HTML
            
        Returns:
            Publication date in YYYY-MM-DD format or None if not found
        """
        # Look for common date meta tags
        meta_tags = [
            {'property': 'article:published_time'},
            {'name': 'publication_date'},
            {'name': 'date'},
            {'name': 'pubdate'},
            {'itemprop': 'datePublished'},
            {'name': 'DC.date.issued'}
        ]
        
        for meta_attrs in meta_tags:
            meta_tag = soup.find('meta', attrs=meta_attrs)
            if meta_tag and meta_tag.get('content'):
                try:
                    # Try to parse the date
                    date_str = meta_tag.get('content')
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return date_obj.strftime('%Y-%m-%d')
                except (ValueError, AttributeError):
                    continue
        
        # Look for time tags
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            try:
                date_str = time_tag.get('datetime')
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return date_obj.strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                pass
        
        # Look for common date patterns in the text
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
            r'(\d{2}\.\d{2}\.\d{4})'  # DD.MM.YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, str(soup))
            if match:
                date_str = match.group(1)
                try:
                    if '-' in date_str:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    elif '/' in date_str:
                        date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    elif '.' in date_str:
                        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def _is_likely_article_url(self, url: str) -> bool:
        """
        Check if a URL is likely to point to an article.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL likely points to an article, False otherwise
        """
        # Common article URL patterns
        article_indicators = [
            r'/article/', r'/story/', r'/news/', r'/post/',
            r'/\d{4}/\d{2}/', r'/blog/', r'/opinion/',
            r'\.html$', r'\.htm$', r'/\d+$'
        ]
        
        # Check if URL matches any article pattern
        for pattern in article_indicators:
            if re.search(pattern, url):
                return True
                
        return False
