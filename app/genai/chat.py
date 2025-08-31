"""Chat completion service for GenAI integration."""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat completions using GenAI models."""
    
    def __init__(self, client: OpenAI, async_client: AsyncOpenAI, model: str):
        """Initialize chat service.
        
        Args:
            client: Synchronous OpenAI client
            async_client: Asynchronous OpenAI client  
            model: Chat model to use
        """
        self.client = client
        self.async_client = async_client
        self.model = model
        
        logger.info(f"Initialized ChatService with model: {model}")
    
    def generate_response(self, 
                         messages: List[Dict[str, str]], 
                         temperature: float = 0.7,
                         max_tokens: Optional[int] = None) -> Optional[str]:
        """Generate a chat response synchronously.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text, or None on error
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                logger.debug(f"Generated response of {len(content)} characters")
                return content
            
            logger.warning("No response choices returned from chat model")
            return None
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return None
    
    async def generate_response_async(self, 
                                    messages: List[Dict[str, str]], 
                                    temperature: float = 0.7,
                                    max_tokens: Optional[int] = None) -> Optional[str]:
        """Generate a chat response asynchronously.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text, or None on error
        """
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                logger.debug(f"Generated response of {len(content)} characters")
                return content
            
            logger.warning("No response choices returned from chat model")
            return None
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return None
    
    async def generate_response_stream(self, 
                                     messages: List[Dict[str, str]], 
                                     temperature: float = 0.7,
                                     max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        """Generate a streaming chat response asynchronously.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            
        Yields:
            Response text chunks
        """
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                        
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"Error: {str(e)}"
    
    def create_messages(self, 
                       system_prompt: str, 
                       user_query: str, 
                       context: Optional[str] = None) -> List[Dict[str, str]]:
        """Create message list for chat completion.
        
        Args:
            system_prompt: System/instruction prompt
            user_query: User's question
            context: Optional context information
            
        Returns:
            List of message dictionaries
        """
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if context:
            messages.append({
                "role": "user", 
                "content": f"Context:\n{context}\n\nQuestion: {user_query}"
            })
        else:
            messages.append({
                "role": "user",
                "content": user_query
            })
        
        return messages
    
    def health_check(self) -> Dict[str, Any]:
        """Check chat service health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Try a simple completion
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'OK' if you can respond."}
            ]
            
            response = self.generate_response(test_messages, temperature=0.0, max_tokens=10)
            
            if response:
                return {
                    'status': 'healthy',
                    'model': self.model,
                    'test_response': response.strip()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'model': self.model,
                    'error': 'No response generated'
                }
                
        except Exception as e:
            logger.error(f"Chat service health check failed: {e}")
            return {
                'status': 'unhealthy',
                'model': self.model,
                'error': str(e)
            }

