import os
import sys
from app.core.scraper import Scraper
import asyncio
import json

async def test_scraper():
    """
    Test the scraper with a few sample URLs to verify functionality.
    """
    # Sample URLs to test
    test_urls = [
        "https://example.com",
        "https://news.ycombinator.com",
        "https://techcrunch.com/2023/01/01/hello-2023/"  # This URL might not exist, just for testing
    ]
    
    print(f"Testing scraper with {len(test_urls)} URLs...")
    
    # Create scraper instance
    scraper = Scraper()
    
    try:
        # Scrape URLs
        articles, errors = await scraper.scrape_urls(test_urls)
        
        # Print results
        print(f"\nSuccessfully scraped {len(articles)} articles")
        for i, article in enumerate(articles):
            print(f"\nArticle {i+1}:")
            print(f"Title: {article.title}")
            print(f"URL: {article.url}")
            print(f"Language: {article.language}")
            print(f"Publication Date: {article.publication_date}")
            print(f"Content (first 150 chars): {article.content[:150]}...")
        
        print(f"\nEncountered {len(errors)} errors")
        for i, error in enumerate(errors):
            print(f"\nError {i+1}:")
            print(f"URL: {error['url']}")
            print(f"Error: {error['error']}")
        
        # Save results to file for inspection
        with open("test_results.json", "w") as f:
            json.dump(
                {
                    "articles": [article.model_dump() for article in articles],
                    "errors": errors
                },
                f,
                indent=2,
                default=str
            )
        
        print("\nTest results saved to test_results.json")
        
    finally:
        # Close scraper
        await scraper.close()

if __name__ == "__main__":
    # Add parent directory to path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    # Run test
    asyncio.run(test_scraper())
