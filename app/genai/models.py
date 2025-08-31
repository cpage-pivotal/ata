"""Model discovery and selection for GenAI services."""

import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class ModelService:
    """Service for discovering and managing GenAI models."""
    
    def __init__(self, client: OpenAI):
        """Initialize model service.
        
        Args:
            client: OpenAI client instance
        """
        self.client = client
        self._cached_models = None
        
        logger.info("Initialized ModelService")
    
    def discover_models(self) -> Dict[str, List[str]]:
        """Discover available models from GenAI service.
        
        Returns:
            Dictionary with categorized model lists
        """
        try:
            if self._cached_models:
                return self._cached_models
            
            models = self.client.models.list()
            model_ids = [model.id for model in models.data] if models.data else []
            
            # Categorize models based on common naming patterns
            categorized = {
                'chat_models': [],
                'embedding_models': [],
                'completion_models': [],
                'other_models': []
            }
            
            for model_id in model_ids:
                model_lower = model_id.lower()
                
                if any(keyword in model_lower for keyword in ['chat', 'gpt', 'claude', 'llama']):
                    categorized['chat_models'].append(model_id)
                elif any(keyword in model_lower for keyword in ['embed', 'ada']):
                    categorized['embedding_models'].append(model_id)
                elif any(keyword in model_lower for keyword in ['complete', 'davinci', 'curie']):
                    categorized['completion_models'].append(model_id)
                else:
                    categorized['other_models'].append(model_id)
            
            self._cached_models = categorized
            logger.info(f"Discovered {len(model_ids)} models: {len(categorized['chat_models'])} chat, {len(categorized['embedding_models'])} embedding")
            
            return categorized
            
        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            return {
                'chat_models': [],
                'embedding_models': [],
                'completion_models': [],
                'other_models': []
            }
    
    def get_best_chat_model(self) -> Optional[str]:
        """Get the best available chat model.
        
        Returns:
            Model ID of the best chat model, or None if none available
        """
        models = self.discover_models()
        chat_models = models.get('chat_models', [])
        
        if not chat_models:
            logger.warning("No chat models available")
            return None
        
        # Preference order for chat models
        preferred_models = [
            'gpt-4',
            'gpt-4-turbo',
            'gpt-3.5-turbo',
            'claude-3',
            'claude-2',
            'llama-2'
        ]
        
        # Find the first preferred model that's available
        for preferred in preferred_models:
            for available in chat_models:
                if preferred in available.lower():
                    logger.info(f"Selected chat model: {available}")
                    return available
        
        # If no preferred model found, use the first available
        selected = chat_models[0]
        logger.info(f"Using first available chat model: {selected}")
        return selected
    
    def get_best_embedding_model(self) -> Optional[str]:
        """Get the best available embedding model.
        
        Returns:
            Model ID of the best embedding model, or None if none available
        """
        models = self.discover_models()
        embedding_models = models.get('embedding_models', [])
        
        if not embedding_models:
            logger.warning("No embedding models available")
            return None
        
        # Preference order for embedding models
        preferred_models = [
            'text-embedding-ada-002',
            'text-embedding-3-large',
            'text-embedding-3-small'
        ]
        
        # Find the first preferred model that's available
        for preferred in preferred_models:
            for available in embedding_models:
                if preferred in available.lower():
                    logger.info(f"Selected embedding model: {available}")
                    return available
        
        # If no preferred model found, use the first available
        selected = embedding_models[0]
        logger.info(f"Using first available embedding model: {selected}")
        return selected
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Model information dictionary
        """
        try:
            model = self.client.models.retrieve(model_id)
            return {
                'id': model.id,
                'object': model.object,
                'created': model.created,
                'owned_by': model.owned_by
            }
            
        except Exception as e:
            logger.error(f"Error getting model info for {model_id}: {e}")
            return {
                'id': model_id,
                'error': str(e)
            }
    
    def clear_cache(self):
        """Clear the cached models list."""
        self._cached_models = None
        logger.info("Cleared model cache")

