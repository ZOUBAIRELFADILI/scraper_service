"""
Fake news detection module using transformer-based models.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import asyncio
from typing import Dict, Any, Tuple
from loguru import logger


class FakeNewsDetector:
    """
    Fake news detector using transformer-based models.
    """
    
    def __init__(self, model_name: str = "roberta-base-openai-detector"):
        """
        Initialize the fake news detector with a pre-trained model.
        
        Args:
            model_name: Name of the pre-trained model to use
        """
        logger.info(f"Initializing fake news detector with model: {model_name}")
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
    
    async def detect_fake_news(self, text: str) -> Tuple[bool, float]:
        """
        Detect if the given text is likely to be fake news.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (is_fake_news, confidence_score)
        """
        # Run the detection in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._detect_fake_news_sync, text
        )
        
        return result
    
    def _detect_fake_news_sync(self, text: str) -> Tuple[bool, float]:
        """
        Detect fake news synchronously (runs in a separate thread).
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (is_fake_news, confidence_score)
        """
        try:
            # Truncate text if it's too long
            max_input_length = self.tokenizer.model_max_length
            if len(text) > max_input_length:
                text = text[:max_input_length]
            
            # Tokenize and get model prediction
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Get probabilities
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # For OpenAI detector, index 1 corresponds to "fake" class
            # Adjust this based on the specific model being used
            fake_prob = probs[0, 1].item()
            
            # Determine if it's fake news based on probability threshold
            is_fake = fake_prob > 0.7  # Adjustable threshold
            
            return is_fake, fake_prob
            
        except Exception as e:
            logger.error(f"Error detecting fake news: {str(e)}")
            # Return default values in case of error
            return False, 0.0
    
    async def enrich_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich an article with fake news detection.
        
        Args:
            article: Article to enrich
            
        Returns:
            Enriched article with fake news detection results
        """
        if not article.get("content"):
            logger.warning(f"Cannot detect fake news in article without content: {article.get('url')}")
            return article
        
        # Create a copy of the article to avoid modifying the original
        enriched = article.copy()
        
        try:
            # Combine title and content for better detection
            text = f"{article.get('title', '')} {article.get('content', '')}"
            is_fake, confidence = await self.detect_fake_news(text)
            
            enriched["is_fake_news"] = is_fake
            enriched["confidence_score"] = confidence
            
        except Exception as e:
            logger.error(f"Error enriching article with fake news detection: {str(e)}")
            enriched["is_fake_news"] = False
            enriched["confidence_score"] = 0.0
        
        return enriched
