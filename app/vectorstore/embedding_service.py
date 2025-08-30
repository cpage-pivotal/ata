"""Embedding service for text-to-vector conversion using GenAI service."""

import logging
import asyncio
from typing import List, Optional
from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings from text using GenAI service."""
    
    def __init__(self, api_key: str, base_url: str, model: str = "text-embedding-ada-002"):
        """Initialize embedding service.
        
        Args:
            api_key: GenAI service API key
            base_url: GenAI service base URL
            model: Embedding model to use
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        
        # Initialize both sync and async clients
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        logger.info(f"Initialized EmbeddingService with model: {model}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding, or None on error
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            # Clean and truncate text if needed (most models have token limits)
            cleaned_text = self._clean_text(text)
            
            response = self.client.embeddings.create(
                input=cleaned_text,
                model=self.model
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)} for text length {len(text)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def generate_embedding_async(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text asynchronously.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding, or None on error
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            cleaned_text = self._clean_text(text)
            
            response = await self.async_client.embeddings.create(
                input=cleaned_text,
                model=self.model
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)} for text length {len(text)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embeddings (or None for failed generations)
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self._process_batch_sync(batch)
            embeddings.extend(batch_embeddings)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        
        return embeddings
    
    async def generate_embeddings_batch_async(self, texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches asynchronously.
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embeddings (or None for failed generations)
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._process_batch_async(batch)
            embeddings.extend(batch_embeddings)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        
        return embeddings
    
    def _process_batch_sync(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Process a batch of texts synchronously."""
        try:
            # Filter and clean texts
            cleaned_texts = [self._clean_text(text) for text in texts if text and text.strip()]
            
            if not cleaned_texts:
                return [None] * len(texts)
            
            response = self.client.embeddings.create(
                input=cleaned_texts,
                model=self.model
            )
            
            # Extract embeddings in order
            embeddings = [data.embedding for data in response.data]
            
            # Fill in None for empty texts
            result = []
            cleaned_idx = 0
            for text in texts:
                if text and text.strip():
                    result.append(embeddings[cleaned_idx])
                    cleaned_idx += 1
                else:
                    result.append(None)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            return [None] * len(texts)
    
    async def _process_batch_async(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Process a batch of texts asynchronously."""
        try:
            # Filter and clean texts
            cleaned_texts = [self._clean_text(text) for text in texts if text and text.strip()]
            
            if not cleaned_texts:
                return [None] * len(texts)
            
            response = await self.async_client.embeddings.create(
                input=cleaned_texts,
                model=self.model
            )
            
            # Extract embeddings in order
            embeddings = [data.embedding for data in response.data]
            
            # Fill in None for empty texts
            result = []
            cleaned_idx = 0
            for text in texts:
                if text and text.strip():
                    result.append(embeddings[cleaned_idx])
                    cleaned_idx += 1
                else:
                    result.append(None)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            return [None] * len(texts)
    
    def _clean_text(self, text: str) -> str:
        """Clean text for embedding generation.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text suitable for embedding
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        cleaned = " ".join(text.split())
        
        # Truncate if too long (approximate token limit)
        # Most embedding models have 8k token limit, roughly 6k characters
        if len(cleaned) > 6000:
            cleaned = cleaned[:6000] + "..."
            logger.warning(f"Text truncated to 6000 characters for embedding")
        
        return cleaned
    
    def health_check(self) -> dict:
        """Check if the embedding service is healthy.
        
        Returns:
            Dictionary with health status
        """
        try:
            # Try to generate a test embedding
            test_embedding = self.generate_embedding("test")
            
            if test_embedding and len(test_embedding) > 0:
                return {
                    "status": "healthy",
                    "model": self.model,
                    "embedding_dimension": len(test_embedding),
                    "base_url": self.base_url
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Failed to generate test embedding",
                    "model": self.model,
                    "base_url": self.base_url
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model,
                "base_url": self.base_url
            }