"""
NLP module for article summarization and keyword extraction.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import yake
from rake_nltk import Rake
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from loguru import logger


class Summarizer:
    """
    Article summarizer using transformer models.
    """
    
    def __init__(self, model_name: str = "t5-small"):
        """
        Initialize the summarizer with a pre-trained model.
        
        Args:
            model_name: Name of the pre-trained model to use
        """
        logger.info(f"Initializing summarizer with model: {model_name}")
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
        
    async def summarize(self, text: str, max_length: int = 150, min_length: int = 40) -> str:
        """
        Generate a summary of the given text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary
            min_length: Minimum length of the summary
            
        Returns:
            Generated summary
        """
        # For T5 models, prepend "summarize: " to the input text
        if "t5" in self.model_name.lower():
            text = f"summarize: {text}"
        
        # Truncate text if it's too long
        max_input_length = self.tokenizer.model_max_length
        if len(text) > max_input_length:
            text = text[:max_input_length]
        
        # Run the summarization in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(
            None, self._generate_summary, text, max_length, min_length
        )
        
        return summary
    
    def _generate_summary(self, text: str, max_length: int, min_length: int) -> str:
        """
        Generate summary using the model (runs in a separate thread).
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary
            min_length: Minimum length of the summary
            
        Returns:
            Generated summary
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True).to(self.device)
        
        # Generate summary
        summary_ids = self.model.generate(
            inputs["input_ids"],
            max_length=max_length,
            min_length=min_length,
            num_beams=4,
            early_stopping=True
        )
        
        # Decode summary
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        return summary


class KeywordExtractor:
    """
    Keyword extractor using multiple algorithms.
    """
    
    def __init__(self):
        """Initialize the keyword extractor with multiple algorithms."""
        logger.info("Initializing keyword extractor")
        self.yake_extractor = yake.KeywordExtractor(
            lan="en", 
            n=2,  # ngram size
            dedupLim=0.9,  # deduplication threshold
            dedupFunc="seqm",  # deduplication function
            windowsSize=1,  # window size
            top=20  # number of keywords to extract
        )
        
        self.rake_extractor = Rake()
        
        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_df=0.85,
            min_df=2,
            max_features=200,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Load spaCy model for NER (optional)
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.spacy_loaded = True
        except:
            logger.warning("spaCy model not found. NER will not be available.")
            self.spacy_loaded = False
    
    async def extract_keywords(self, text: str, method: str = "combined", num_keywords: int = 10) -> List[str]:
        """
        Extract keywords from the given text.
        
        Args:
            text: Text to extract keywords from
            method: Keyword extraction method ('yake', 'rake', 'tfidf', 'ner', or 'combined')
            num_keywords: Number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        # Run the extraction in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        keywords = await loop.run_in_executor(
            None, self._extract_keywords_sync, text, method, num_keywords
        )
        
        return keywords
    
    def _extract_keywords_sync(self, text: str, method: str, num_keywords: int) -> List[str]:
        """
        Extract keywords synchronously (runs in a separate thread).
        
        Args:
            text: Text to extract keywords from
            method: Keyword extraction method
            num_keywords: Number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        if method == "yake":
            return self._extract_with_yake(text, num_keywords)
        elif method == "rake":
            return self._extract_with_rake(text, num_keywords)
        elif method == "tfidf":
            return self._extract_with_tfidf(text, num_keywords)
        elif method == "ner":
            return self._extract_with_ner(text, num_keywords)
        elif method == "combined":
            # Combine results from multiple methods
            yake_keywords = set(self._extract_with_yake(text, num_keywords))
            rake_keywords = set(self._extract_with_rake(text, num_keywords))
            
            # Combine and deduplicate
            combined = list(yake_keywords.union(rake_keywords))
            
            # Add NER if available
            if self.spacy_loaded:
                ner_keywords = set(self._extract_with_ner(text, num_keywords))
                combined = list(set(combined).union(ner_keywords))
            
            # Sort by length (shorter keywords first) and return top N
            return sorted(combined, key=len)[:num_keywords]
        else:
            logger.warning(f"Unknown keyword extraction method: {method}. Using YAKE.")
            return self._extract_with_yake(text, num_keywords)
    
    def _extract_with_yake(self, text: str, num_keywords: int) -> List[str]:
        """Extract keywords using YAKE algorithm."""
        try:
            keywords = self.yake_extractor.extract_keywords(text)
            # YAKE returns (keyword, score) tuples, lower score is better
            return [kw for kw, _ in sorted(keywords, key=lambda x: x[1])[:num_keywords]]
        except Exception as e:
            logger.error(f"Error extracting keywords with YAKE: {str(e)}")
            return []
    
    def _extract_with_rake(self, text: str, num_keywords: int) -> List[str]:
        """Extract keywords using RAKE algorithm."""
        try:
            self.rake_extractor.extract_keywords_from_text(text)
            keywords = self.rake_extractor.get_ranked_phrases()
            return keywords[:num_keywords]
        except Exception as e:
            logger.error(f"Error extracting keywords with RAKE: {str(e)}")
            return []
    
    def _extract_with_tfidf(self, text: str, num_keywords: int) -> List[str]:
        """Extract keywords using TF-IDF."""
        try:
            # TF-IDF works better with a corpus, but we can use it with a single document
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text])
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Get top N features with highest TF-IDF scores
            scores = zip(feature_names, tfidf_matrix.toarray()[0])
            sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
            
            return [word for word, _ in sorted_scores[:num_keywords]]
        except Exception as e:
            logger.error(f"Error extracting keywords with TF-IDF: {str(e)}")
            return []
    
    def _extract_with_ner(self, text: str, num_keywords: int) -> List[str]:
        """Extract named entities as keywords."""
        if not self.spacy_loaded:
            return []
        
        try:
            doc = self.nlp(text)
            entities = [ent.text for ent in doc.ents]
            
            # Deduplicate and get top N
            unique_entities = list(set(entities))
            return unique_entities[:num_keywords]
        except Exception as e:
            logger.error(f"Error extracting named entities: {str(e)}")
            return []


class NLPEnricher:
    """
    NLP enrichment pipeline for articles.
    """
    
    def __init__(self, summarizer_model: str = "t5-small"):
        """
        Initialize the NLP enrichment pipeline.
        
        Args:
            summarizer_model: Name of the pre-trained model to use for summarization
        """
        logger.info("Initializing NLP enrichment pipeline")
        self.summarizer = Summarizer(model_name=summarizer_model)
        self.keyword_extractor = KeywordExtractor()
    
    async def enrich_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich an article with NLP features.
        
        Args:
            article: Article to enrich
            
        Returns:
            Enriched article
        """
        if not article.get("content"):
            logger.warning(f"Cannot enrich article without content: {article.get('url')}")
            return article
        
        # Create a copy of the article to avoid modifying the original
        enriched = article.copy()
        
        # Generate summary
        try:
            summary = await self.summarizer.summarize(article["content"])
            enriched["summary"] = summary
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            enriched["summary"] = None
        
        # Extract keywords
        try:
            keywords = await self.keyword_extractor.extract_keywords(article["content"])
            enriched["keywords"] = keywords
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            enriched["keywords"] = []
        
        return enriched
