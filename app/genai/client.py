"""GenAI client for Tanzu Platform integration."""

import logging
from typing import Optional, Dict, Any
from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)


class GenAIClient:
    """Client for GenAI on Tanzu Platform services."""
    
    def __init__(self, api_key: str, base_url: str):
        """Initialize GenAI client.
        
        Args:
            api_key: GenAI service API key
            base_url: GenAI service base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        
        # Initialize both sync and async clients
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        logger.info(f"Initialized GenAI client with base URL: {base_url}")
    
    def get_sync_client(self) -> OpenAI:
        """Get synchronous OpenAI client."""
        return self.client
    
    def get_async_client(self) -> AsyncOpenAI:
        """Get asynchronous OpenAI client."""
        return self.async_client
    
    def health_check(self) -> Dict[str, Any]:
        """Check GenAI service health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Try to list models to test connectivity
            models = self.client.models.list()
            model_count = len(models.data) if models.data else 0
            
            return {
                'status': 'healthy',
                'base_url': self.base_url,
                'available_models': model_count,
                'connection': 'ok'
            }
            
        except Exception as e:
            logger.error(f"GenAI health check failed: {e}")
            return {
                'status': 'unhealthy',
                'base_url': self.base_url,
                'error': str(e),
                'connection': 'error'
            }

