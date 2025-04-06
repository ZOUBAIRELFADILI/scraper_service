"""
Test script for the enhanced scraper service.
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pipeline import Pipeline
from app.nlp.enrichment import NLPEnricher
from app.fakenews.detector import FakeNewsDetector
from app.db.mongodb import MongoDBClient
from app.utils.date_filters.filters import is_recent_article
from app.utils.url_cleaners.normalizer import normalize_url


async def test_pipeline():
    """Test the complete pipeline with a sample URL."""
    print("\n=== Testing Complete Pipeline ===")
    
    # Initialize pipeline
    pipeline = Pipeline(store_in_db=True)
    
    # Test URLs
    test_urls = [
        "https://example.com",
        "https://news.ycombinator.com",
        "https://en.wikipedia.org/wiki/Artificial_intelligence"
    ]
    
    try:
        # Process URLs
        print(f"Processing {len(test_urls)} URLs...")
        articles, errors = await pipeline.process_urls(test_urls)
        
        # Print results
        print(f"\nProcessed {len(articles)} articles with {len(errors)} errors")
        
        if articles:
            # Print first article details
            article = articles[0]
            print("\nSample Article:")
            print(f"Title: {article.get('title')}")
            print(f"URL: {article.get('url')}")
            print(f"Language: {article.get('language')}")
            print(f"Publication Date: {article.get('publication_date')}")
            print(f"Summary: {article.get('summary')[:100]}..." if article.get('summary') else "No summary")
            print(f"Keywords: {', '.join(article.get('keywords')[:5])}..." if article.get('keywords') else "No keywords")
            print(f"Is Fake News: {article.get('is_fake_news')}")
            print(f"Confidence Score: {article.get('confidence_score')}")
            print(f"Images: {len(article.get('image_urls', []))} found")
            print(f"Logo URL: {article.get('logo_url')}")
            
            # Save article to file for inspection
            with open("test_article.json", "w") as f:
                json.dump(article, f, indent=2, default=str)
            print("\nSaved complete article to test_article.json")
        
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"URL: {error.get('url')}")
                print(f"Error: {error.get('error')}")
                print()
        
        return len(articles) > 0
    
    except Exception as e:
        print(f"Error testing pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Close pipeline
        await pipeline.close()


async def test_nlp_enrichment():
    """Test NLP enrichment with a sample text."""
    print("\n=== Testing NLP Enrichment ===")
    
    # Sample article
    article = {
        "title": "Artificial Intelligence Advances",
        "content": """
        Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to natural intelligence displayed by animals including humans. 
        AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.
        
        The term "artificial intelligence" had previously been used to describe machines that mimic and display "human" cognitive skills that are associated with the human mind, such as "learning" and "problem-solving". This definition has since been rejected by major AI researchers who now describe AI in terms of rationality and acting rationally, which does not limit how intelligence can be articulated.
        
        AI applications include advanced web search engines (e.g., Google), recommendation systems (used by YouTube, Amazon and Netflix), understanding human speech (such as Siri and Alexa), self-driving cars (e.g., Waymo), generative or creative tools (ChatGPT and AI art), automated decision-making and competing at the highest level in strategic game systems (such as chess and Go).
        
        As machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology.
        """,
        "url": "https://example.com/ai-article",
        "language": "en"
    }
    
    try:
        # Initialize NLP enricher
        enricher = NLPEnricher()
        
        # Enrich article
        print("Enriching article...")
        enriched = await enricher.enrich_article(article)
        
        # Print results
        print("\nEnriched Article:")
        print(f"Summary: {enriched.get('summary')}")
        print(f"Keywords: {', '.join(enriched.get('keywords'))}")
        
        return enriched.get('summary') and enriched.get('keywords')
    
    except Exception as e:
        print(f"Error testing NLP enrichment: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_fake_news_detection():
    """Test fake news detection with sample texts."""
    print("\n=== Testing Fake News Detection ===")
    
    # Sample articles
    real_article = {
        "title": "NASA Confirms Water on Mars",
        "content": """
        NASA scientists have confirmed the presence of water on Mars. The discovery was made using data from the Mars Reconnaissance Orbiter, 
        which detected hydrated salts on the slopes of Martian craters. This finding suggests that liquid water flows on the present-day Mars.
        The discovery is significant because it could have implications for the potential for life on Mars.
        """
    }
    
    fake_article = {
        "title": "Scientists Discover Dragons in Remote Mountain Range",
        "content": """
        A team of scientists claims to have discovered living dragons in a remote mountain range. The creatures, which can reportedly breathe fire 
        and fly at speeds of up to 200 mph, have been hiding from human civilization for centuries. Experts are now debating whether these dragons 
        should be classified as reptiles or as a completely new class of animal. The government has established a no-fly zone over the area.
        """
    }
    
    try:
        # Initialize fake news detector
        detector = FakeNewsDetector()
        
        # Test real article
        print("Testing real article...")
        real_result = await detector.enrich_article(real_article)
        print(f"Is Fake News: {real_result.get('is_fake_news')}")
        print(f"Confidence Score: {real_result.get('confidence_score')}")
        
        # Test fake article
        print("\nTesting fake article...")
        fake_result = await detector.enrich_article(fake_article)
        print(f"Is Fake News: {fake_result.get('is_fake_news')}")
        print(f"Confidence Score: {fake_result.get('confidence_score')}")
        
        return True
    
    except Exception as e:
        print(f"Error testing fake news detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_mongodb():
    """Test MongoDB integration."""
    print("\n=== Testing MongoDB Integration ===")
    
    # Sample article
    article = {
        "title": "Test Article",
        "content": "This is a test article for MongoDB integration.",
        "summary": "Test article summary.",
        "keywords": ["test", "mongodb", "integration"],
        "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        "logo_url": "https://example.com/logo.png",
        "publication_date": datetime.utcnow().isoformat(),
        "language": "en",
        "url": f"https://example.com/test-article-{datetime.utcnow().timestamp()}",
        "source_domain": "example.com",
        "is_fake_news": False,
        "confidence_score": 0.1
    }
    
    try:
        # Initialize MongoDB client
        db_client = MongoDBClient()
        
        # Store article
        print("Storing article...")
        article_id = await db_client.store_article(article)
        print(f"Stored article with ID: {article_id}")
        
        # Retrieve article
        print("\nRetrieving article...")
        retrieved = await db_client.get_article(article_id)
        print(f"Retrieved article: {retrieved.get('title')}")
        
        # Search articles
        print("\nSearching articles...")
        search_results = await db_client.search_articles("test")
        print(f"Found {len(search_results.get('articles', []))} articles matching 'test'")
        
        return article_id and retrieved and search_results.get('articles')
    
    except Exception as e:
        print(f"Error testing MongoDB integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_date_filtering():
    """Test date filtering."""
    print("\n=== Testing Date Filtering ===")
    
    from datetime import datetime, timedelta
    
    # Sample articles
    recent_article = {
        "title": "Recent Article",
        "publication_date": datetime.utcnow().isoformat()
    }
    
    old_article = {
        "title": "Old Article",
        "publication_date": (datetime.utcnow() - timedelta(days=200)).isoformat()
    }
    
    no_date_article = {
        "title": "No Date Article"
    }
    
    try:
        # Test recent article
        print("Testing recent article...")
        is_recent = is_recent_article(recent_article)
        print(f"Is recent: {is_recent}")
        
        # Test old article
        print("\nTesting old article...")
        is_recent = is_recent_article(old_article)
        print(f"Is recent: {is_recent}")
        
        # Test article with no date
        print("\nTesting article with no date...")
        is_recent = is_recent_article(no_date_article)
        print(f"Is recent: {is_recent}")
        
        return True
    
    except Exception as e:
        print(f"Error testing date filtering: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_tests():
    """Run all tests."""
    print("=== Running Tests for Enhanced Scraper Service ===\n")
    
    tests = [
        ("NLP Enrichment", test_nlp_enrichment),
        ("Fake News Detection", test_fake_news_detection),
        ("Date Filtering", test_date_filtering),
        ("MongoDB Integration", test_mongodb),
        ("Complete Pipeline", test_pipeline)
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"\n{'=' * 50}")
        print(f"Running test: {name}")
        print(f"{'=' * 50}")
        
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Test {name} failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n\n=== Test Summary ===")
    all_passed = True
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        if not result:
            all_passed = False
        print(f"{name}: {status}")
    
    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed. Check the logs for details.")


if __name__ == "__main__":
    asyncio.run(run_tests())
