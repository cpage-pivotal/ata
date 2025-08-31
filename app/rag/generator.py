"""Response generation component for RAG pipeline."""

import logging
from typing import List, Dict, Any, Optional
from ..genai.chat import ChatService
from .prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class Generator:
    """Response generation component using chat models."""
    
    def __init__(self, chat_service: ChatService):
        """Initialize generator.
        
        Args:
            chat_service: Chat service for generating responses
        """
        self.chat_service = chat_service
        self.prompt_templates = PromptTemplates()
        
        logger.info("Initialized Generator")
    
    async def generate_response(self, 
                              query: str,
                              reports: List[Dict[str, Any]],
                              temperature: float = 0.7,
                              max_tokens: Optional[int] = 1500) -> Dict[str, Any]:
        """Generate a response to the user's query using retrieved reports.
        
        Args:
            query: User's question
            reports: List of relevant maintenance reports
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            if not reports:
                return await self._generate_no_context_response(query, temperature, max_tokens)
            
            # Format context from reports
            context = self.prompt_templates.format_context_from_reports(reports)
            
            # Select appropriate prompt template
            user_prompt = self.prompt_templates.select_template(query, context, reports)
            
            # Create messages for chat completion
            messages = self.chat_service.create_messages(
                system_prompt=self.prompt_templates.get_system_prompt(),
                user_query=user_prompt
            )
            
            # Generate response
            response_text = await self.chat_service.generate_response_async(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if not response_text:
                logger.error("Failed to generate response from chat service")
                return self._create_error_response("Failed to generate response")
            
            # Create source citations
            sources = self.prompt_templates.create_source_citations(reports)
            
            # Calculate confidence score based on similarity scores
            confidence_score = self._calculate_confidence_score(reports)
            
            return {
                'response': response_text,
                'sources': sources,
                'confidence_score': confidence_score,
                'query_type': self.prompt_templates.detect_query_type(query),
                'total_sources_used': len(reports),
                'generation_successful': True
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._create_error_response(f"Generation error: {str(e)}")
    
    async def generate_streaming_response(self, 
                                        query: str,
                                        reports: List[Dict[str, Any]],
                                        temperature: float = 0.7,
                                        max_tokens: Optional[int] = 1500):
        """Generate a streaming response to the user's query.
        
        Args:
            query: User's question
            reports: List of relevant maintenance reports
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens in response
            
        Yields:
            Response text chunks
        """
        try:
            if not reports:
                yield "I don't have any relevant maintenance reports to answer your question. "
                yield "Please try rephrasing your query or check if reports have been uploaded to the system."
                return
            
            # Format context from reports
            context = self.prompt_templates.format_context_from_reports(reports)
            
            # Select appropriate prompt template
            user_prompt = self.prompt_templates.select_template(query, context, reports)
            
            # Create messages for chat completion
            messages = self.chat_service.create_messages(
                system_prompt=self.prompt_templates.get_system_prompt(),
                user_query=user_prompt
            )
            
            # Generate streaming response
            async for chunk in self.chat_service.generate_response_stream(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"Error generating response: {str(e)}"
    
    async def generate_safety_critical_response(self, 
                                              query: str,
                                              reports: List[Dict[str, Any]],
                                              temperature: float = 0.3) -> Dict[str, Any]:
        """Generate a response for safety-critical queries with lower temperature.
        
        Args:
            query: User's safety-related question
            reports: List of relevant maintenance reports
            temperature: Lower temperature for more consistent responses
            
        Returns:
            Dictionary with response and safety metadata
        """
        try:
            if not reports:
                return await self._generate_safety_no_context_response(query)
            
            # Format context from reports
            context = self.prompt_templates.format_context_from_reports(reports)
            
            # Use safety-critical template
            user_prompt = self.prompt_templates.format_safety_critical_query(query, context)
            
            # Create messages with safety emphasis
            messages = self.chat_service.create_messages(
                system_prompt=self.prompt_templates.get_system_prompt(),
                user_query=user_prompt
            )
            
            # Generate response with lower temperature for consistency
            response_text = await self.chat_service.generate_response_async(
                messages=messages,
                temperature=temperature,
                max_tokens=2000  # Allow longer responses for safety analysis
            )
            
            if not response_text:
                return self._create_error_response("Failed to generate safety-critical response")
            
            # Create source citations with safety emphasis
            sources = self.prompt_templates.create_source_citations(reports)
            
            # Add safety metadata
            safety_critical_count = sum(1 for r in reports if r.get('safety_critical', 'false').lower() == 'true')
            high_severity_count = sum(1 for r in reports if r.get('severity', '').lower() in ['major', 'critical'])
            
            return {
                'response': response_text,
                'sources': sources,
                'confidence_score': self._calculate_confidence_score(reports),
                'query_type': 'safety_critical',
                'total_sources_used': len(reports),
                'safety_metadata': {
                    'safety_critical_reports': safety_critical_count,
                    'high_severity_reports': high_severity_count,
                    'safety_warning': True
                },
                'generation_successful': True
            }
            
        except Exception as e:
            logger.error(f"Error generating safety-critical response: {e}")
            return self._create_error_response(f"Safety-critical generation error: {str(e)}")
    
    async def generate_trend_analysis_response(self, 
                                             query: str,
                                             reports: List[Dict[str, Any]],
                                             temperature: float = 0.5) -> Dict[str, Any]:
        """Generate a response for trend analysis queries.
        
        Args:
            query: User's trend analysis question
            reports: List of relevant maintenance reports
            temperature: Medium temperature for balanced creativity/consistency
            
        Returns:
            Dictionary with response and trend metadata
        """
        try:
            if not reports:
                return await self._generate_no_context_response(query, temperature)
            
            # Format context from reports
            context = self.prompt_templates.format_context_from_reports(reports)
            
            # Use trend analysis template
            user_prompt = self.prompt_templates.format_trend_analysis(query, context)
            
            # Create messages
            messages = self.chat_service.create_messages(
                system_prompt=self.prompt_templates.get_system_prompt(),
                user_query=user_prompt
            )
            
            # Generate response
            response_text = await self.chat_service.generate_response_async(
                messages=messages,
                temperature=temperature,
                max_tokens=2000  # Allow longer responses for trend analysis
            )
            
            if not response_text:
                return self._create_error_response("Failed to generate trend analysis response")
            
            # Create source citations
            sources = self.prompt_templates.create_source_citations(reports)
            
            # Calculate trend metadata
            trend_metadata = self._calculate_trend_metadata(reports)
            
            return {
                'response': response_text,
                'sources': sources,
                'confidence_score': self._calculate_confidence_score(reports),
                'query_type': 'trend_analysis',
                'total_sources_used': len(reports),
                'trend_metadata': trend_metadata,
                'generation_successful': True
            }
            
        except Exception as e:
            logger.error(f"Error generating trend analysis response: {e}")
            return self._create_error_response(f"Trend analysis generation error: {str(e)}")
    
    def _calculate_confidence_score(self, reports: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on retrieved reports.
        
        Args:
            reports: List of maintenance reports with similarity scores
            
        Returns:
            Confidence score between 0 and 1
        """
        if not reports:
            return 0.0
        
        # Base confidence on average similarity score
        similarity_scores = [r.get('similarity_score', 0.0) for r in reports]
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        
        # Boost confidence if we have multiple relevant reports
        count_boost = min(len(reports) / 10.0, 0.2)  # Up to 0.2 boost for 10+ reports
        
        # Boost confidence for safety-critical or high-severity reports
        safety_boost = 0.0
        for report in reports:
            if report.get('safety_critical', 'false').lower() == 'true':
                safety_boost += 0.05
            elif report.get('severity', '').lower() in ['major', 'critical']:
                safety_boost += 0.03
        
        safety_boost = min(safety_boost, 0.15)  # Cap safety boost
        
        # Calculate final confidence
        confidence = min(avg_similarity + count_boost + safety_boost, 1.0)
        
        return round(confidence, 3)
    
    def _calculate_trend_metadata(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metadata for trend analysis.
        
        Args:
            reports: List of maintenance reports
            
        Returns:
            Dictionary with trend metadata
        """
        if not reports:
            return {}
        
        # Count by ATA chapter
        ata_counts = {}
        for report in reports:
            ata_chapter = report.get('ata_chapter', 'Unknown')
            ata_counts[ata_chapter] = ata_counts.get(ata_chapter, 0) + 1
        
        # Count by severity
        severity_counts = {}
        for report in reports:
            severity = report.get('severity', 'Unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by defect type
        defect_counts = {}
        for report in reports:
            defect_types = report.get('defect_types', [])
            for defect_type in defect_types:
                defect_counts[defect_type] = defect_counts.get(defect_type, 0) + 1
        
        return {
            'total_reports_analyzed': len(reports),
            'ata_chapter_distribution': ata_counts,
            'severity_distribution': severity_counts,
            'defect_type_distribution': defect_counts,
            'date_range': self._get_date_range(reports)
        }
    
    def _get_date_range(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get date range from reports.
        
        Args:
            reports: List of maintenance reports
            
        Returns:
            Dictionary with date range information
        """
        dates = []
        for report in reports:
            created_at = report.get('created_at')
            if created_at:
                dates.append(created_at)
        
        if not dates:
            return {'earliest': None, 'latest': None}
        
        dates.sort()
        return {
            'earliest': dates[0],
            'latest': dates[-1],
            'span_days': None  # Could calculate if needed
        }
    
    async def _generate_no_context_response(self, query: str, temperature: float, max_tokens: Optional[int] = 1000) -> Dict[str, Any]:
        """Generate response when no relevant reports are found.
        
        Args:
            query: User's question
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            Dictionary with no-context response
        """
        no_context_prompt = f"""The user asked: "{query}"

However, no relevant maintenance reports were found in the database to answer this question.

Please provide a helpful response that:
1. Acknowledges that no specific maintenance reports were found
2. Provides general aviation maintenance guidance if applicable
3. Suggests how the user might refine their query
4. Mentions that more reports may need to be uploaded to the system

Keep the response professional and helpful."""
        
        messages = self.chat_service.create_messages(
            system_prompt=self.prompt_templates.get_system_prompt(),
            user_query=no_context_prompt
        )
        
        response_text = await self.chat_service.generate_response_async(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'response': response_text or "I don't have any relevant maintenance reports to answer your question. Please try rephrasing your query or ensure that relevant reports have been uploaded to the system.",
            'sources': [],
            'confidence_score': 0.0,
            'query_type': 'no_context',
            'total_sources_used': 0,
            'generation_successful': bool(response_text)
        }
    
    async def _generate_safety_no_context_response(self, query: str) -> Dict[str, Any]:
        """Generate safety-focused response when no reports are found.
        
        Args:
            query: User's safety question
            
        Returns:
            Dictionary with safety no-context response
        """
        safety_response = """⚠️ SAFETY NOTICE ⚠️

No specific maintenance reports were found to answer your safety-related question. 

For safety-critical maintenance issues:
1. Consult official maintenance manuals and procedures
2. Contact certified maintenance personnel immediately
3. Follow all regulatory requirements (FAA, EASA, etc.)
4. Do not proceed with maintenance actions without proper authorization

This system is for informational purposes only and should not be used as the sole source for safety-critical decisions."""
        
        return {
            'response': safety_response,
            'sources': [],
            'confidence_score': 0.0,
            'query_type': 'safety_critical',
            'total_sources_used': 0,
            'safety_metadata': {
                'safety_critical_reports': 0,
                'high_severity_reports': 0,
                'safety_warning': True
            },
            'generation_successful': True
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response.
        
        Args:
            error_message: Error description
            
        Returns:
            Dictionary with error response
        """
        return {
            'response': f"I apologize, but I encountered an error while processing your request: {error_message}. Please try again or contact support if the issue persists.",
            'sources': [],
            'confidence_score': 0.0,
            'query_type': 'error',
            'total_sources_used': 0,
            'generation_successful': False,
            'error': error_message
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check generator health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Test chat service
            chat_health = self.chat_service.health_check()
            
            return {
                'status': 'healthy' if chat_health.get('status') == 'healthy' else 'unhealthy',
                'chat_service_status': chat_health.get('status', 'unknown'),
                'model': chat_health.get('model', 'unknown'),
                'prompt_templates': 'loaded'
            }
            
        except Exception as e:
            logger.error(f"Generator health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
