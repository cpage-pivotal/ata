"""RAG Pipeline orchestrator for Boeing Aircraft Maintenance Report System."""

import logging
import time
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime

from .retriever import Retriever
from .generator import Generator
from ..vectorstore.vectorstore_service import VectorStoreService

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Complete RAG pipeline orchestrating retrieval and generation."""
    
    def __init__(self, retriever: Retriever, generator: Generator, vector_store: VectorStoreService):
        """Initialize RAG pipeline.
        
        Args:
            retriever: Retrieval component
            generator: Generation component
            vector_store: Vector store for query history
        """
        self.retriever = retriever
        self.generator = generator
        self.vector_store = vector_store
        
        logger.info("Initialized RAG Pipeline")
    
    async def process_query(self, 
                          query: str,
                          max_results: int = 10,
                          similarity_threshold: float = 0.5,
                          temperature: float = 0.7,
                          filters: Optional[Dict[str, Any]] = None,
                          store_query: bool = True) -> Dict[str, Any]:
        """Process a complete RAG query with retrieval and generation.
        
        Args:
            query: User's question
            max_results: Maximum number of reports to retrieve
            similarity_threshold: Minimum similarity score for retrieval
            temperature: Generation temperature
            filters: Optional filters for retrieval
            store_query: Whether to store query in history
            
        Returns:
            Complete RAG response with metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing RAG query: '{query[:50]}...'")
            
            # Step 1: Retrieve relevant reports
            retrieval_start = time.time()
            reports = await self.retriever.retrieve_relevant_reports(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold,
                filters=filters
            )
            retrieval_time = int((time.time() - retrieval_start) * 1000)
            
            logger.info(f"Retrieved {len(reports)} reports in {retrieval_time}ms")
            
            # Step 2: Generate response
            generation_start = time.time()
            response_data = await self.generator.generate_response(
                query=query,
                reports=reports,
                temperature=temperature
            )
            generation_time = int((time.time() - generation_start) * 1000)
            
            logger.info(f"Generated response in {generation_time}ms")
            
            # Step 3: Compile complete response
            total_time = int((time.time() - start_time) * 1000)
            
            complete_response = {
                'query_id': f"rag_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                'query_text': query,
                'response': response_data.get('response', ''),
                'sources': response_data.get('sources', []),
                'metadata': {
                    'processing_time_ms': total_time,
                    'retrieval_time_ms': retrieval_time,
                    'generation_time_ms': generation_time,
                    'total_sources_considered': len(reports),
                    'confidence_score': response_data.get('confidence_score', 0.0),
                    'query_type': response_data.get('query_type', 'general'),
                    'model_used': 'rag_pipeline',
                    'filters_applied': filters or {},
                    'similarity_threshold': similarity_threshold,
                    'temperature': temperature
                },
                'timestamp': datetime.utcnow().isoformat(),
                'generation_successful': response_data.get('generation_successful', False)
            }
            
            # Add any additional metadata from generation
            if 'safety_metadata' in response_data:
                complete_response['metadata']['safety_metadata'] = response_data['safety_metadata']
            if 'trend_metadata' in response_data:
                complete_response['metadata']['trend_metadata'] = response_data['trend_metadata']
            
            # Step 4: Store query in history if requested
            if store_query and response_data.get('generation_successful', False):
                try:
                    await self.vector_store.store_query(
                        query_text=query,
                        response_text=response_data.get('response', ''),
                        sources=response_data.get('sources', []),
                        processing_time_ms=total_time
                    )
                except Exception as e:
                    logger.warning(f"Failed to store query in history: {e}")
            
            logger.info(f"RAG query processed successfully in {total_time}ms")
            return complete_response
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return self._create_error_response(query, str(e), int((time.time() - start_time) * 1000))
    
    async def process_streaming_query(self, 
                                    query: str,
                                    max_results: int = 10,
                                    similarity_threshold: float = 0.5,
                                    temperature: float = 0.7,
                                    filters: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a streaming RAG query.
        
        Args:
            query: User's question
            max_results: Maximum number of reports to retrieve
            similarity_threshold: Minimum similarity score for retrieval
            temperature: Generation temperature
            filters: Optional filters for retrieval
            
        Yields:
            Streaming response chunks with metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing streaming RAG query: '{query[:50]}...'")
            
            # Step 1: Retrieve relevant reports
            reports = await self.retriever.retrieve_relevant_reports(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold,
                filters=filters
            )
            
            # Yield initial metadata
            yield {
                'type': 'metadata',
                'query_id': f"rag_stream_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                'query_text': query,
                'sources_found': len(reports),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Step 2: Stream response generation
            async for chunk in self.generator.generate_streaming_response(
                query=query,
                reports=reports,
                temperature=temperature
            ):
                yield {
                    'type': 'content',
                    'chunk': chunk
                }
            
            # Yield final metadata
            total_time = int((time.time() - start_time) * 1000)
            yield {
                'type': 'final_metadata',
                'processing_time_ms': total_time,
                'sources': self.generator.prompt_templates.create_source_citations(reports),
                'confidence_score': self.generator._calculate_confidence_score(reports)
            }
            
        except Exception as e:
            logger.error(f"Error in streaming RAG pipeline: {e}")
            yield {
                'type': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def process_safety_critical_query(self, 
                                          query: str,
                                          max_results: int = 15,
                                          similarity_threshold: float = 0.4) -> Dict[str, Any]:
        """Process a safety-critical query with enhanced retrieval and generation.
        
        Args:
            query: User's safety-related question
            max_results: Maximum number of reports to retrieve
            similarity_threshold: Minimum similarity score
            
        Returns:
            Safety-focused RAG response
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing safety-critical query: '{query[:50]}...'")
            
            # Retrieve safety-critical reports
            reports = await self.retriever.retrieve_safety_critical(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            # Generate safety-focused response
            response_data = await self.generator.generate_safety_critical_response(
                query=query,
                reports=reports
            )
            
            # Compile response with safety emphasis
            total_time = int((time.time() - start_time) * 1000)
            
            complete_response = {
                'query_id': f"safety_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                'query_text': query,
                'response': response_data.get('response', ''),
                'sources': response_data.get('sources', []),
                'metadata': {
                    'processing_time_ms': total_time,
                    'total_sources_considered': len(reports),
                    'confidence_score': response_data.get('confidence_score', 0.0),
                    'query_type': 'safety_critical',
                    'model_used': 'rag_pipeline_safety',
                    'safety_metadata': response_data.get('safety_metadata', {}),
                    'temperature': 0.3  # Lower temperature for safety queries
                },
                'timestamp': datetime.utcnow().isoformat(),
                'generation_successful': response_data.get('generation_successful', False),
                'safety_warning': True
            }
            
            # Store safety query
            if response_data.get('generation_successful', False):
                try:
                    await self.vector_store.store_query(
                        query_text=query,
                        response_text=response_data.get('response', ''),
                        sources=response_data.get('sources', []),
                        processing_time_ms=total_time,
                        query_type="safety_critical"
                    )
                except Exception as e:
                    logger.warning(f"Failed to store safety query: {e}")
            
            return complete_response
            
        except Exception as e:
            logger.error(f"Error in safety-critical RAG pipeline: {e}")
            return self._create_error_response(query, str(e), int((time.time() - start_time) * 1000))
    
    async def process_trend_analysis_query(self, 
                                         query: str,
                                         max_results: int = 20,
                                         similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """Process a trend analysis query with enhanced data retrieval.
        
        Args:
            query: User's trend analysis question
            max_results: Maximum number of reports to retrieve
            similarity_threshold: Lower threshold for more data points
            
        Returns:
            Trend analysis RAG response
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing trend analysis query: '{query[:50]}...'")
            
            # Retrieve reports for trend analysis
            reports = await self.retriever.retrieve_for_trend_analysis(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            # Generate trend analysis response
            response_data = await self.generator.generate_trend_analysis_response(
                query=query,
                reports=reports
            )
            
            # Compile response with trend metadata
            total_time = int((time.time() - start_time) * 1000)
            
            complete_response = {
                'query_id': f"trend_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                'query_text': query,
                'response': response_data.get('response', ''),
                'sources': response_data.get('sources', []),
                'metadata': {
                    'processing_time_ms': total_time,
                    'total_sources_considered': len(reports),
                    'confidence_score': response_data.get('confidence_score', 0.0),
                    'query_type': 'trend_analysis',
                    'model_used': 'rag_pipeline_trend',
                    'trend_metadata': response_data.get('trend_metadata', {}),
                    'temperature': 0.5
                },
                'timestamp': datetime.utcnow().isoformat(),
                'generation_successful': response_data.get('generation_successful', False)
            }
            
            return complete_response
            
        except Exception as e:
            logger.error(f"Error in trend analysis RAG pipeline: {e}")
            return self._create_error_response(query, str(e), int((time.time() - start_time) * 1000))
    
    async def process_ata_specific_query(self, 
                                       query: str,
                                       ata_chapter: str,
                                       max_results: int = 10,
                                       similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """Process a query specific to an ATA chapter.
        
        Args:
            query: User's question
            ata_chapter: ATA chapter to focus on
            max_results: Maximum number of reports to retrieve
            similarity_threshold: Minimum similarity score
            
        Returns:
            ATA-specific RAG response
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing ATA {ata_chapter} query: '{query[:50]}...'")
            
            # Retrieve reports from specific ATA chapter
            reports = await self.retriever.retrieve_by_ata_chapter(
                query=query,
                ata_chapter=ata_chapter,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            # Generate response
            response_data = await self.generator.generate_response(
                query=query,
                reports=reports,
                temperature=0.6  # Slightly lower temperature for technical accuracy
            )
            
            # Compile response
            total_time = int((time.time() - start_time) * 1000)
            
            complete_response = {
                'query_id': f"ata_{ata_chapter}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                'query_text': query,
                'response': response_data.get('response', ''),
                'sources': response_data.get('sources', []),
                'metadata': {
                    'processing_time_ms': total_time,
                    'total_sources_considered': len(reports),
                    'confidence_score': response_data.get('confidence_score', 0.0),
                    'query_type': 'ata_specific',
                    'model_used': 'rag_pipeline_ata',
                    'ata_chapter': ata_chapter,
                    'temperature': 0.6
                },
                'timestamp': datetime.utcnow().isoformat(),
                'generation_successful': response_data.get('generation_successful', False)
            }
            
            return complete_response
            
        except Exception as e:
            logger.error(f"Error in ATA-specific RAG pipeline: {e}")
            return self._create_error_response(query, str(e), int((time.time() - start_time) * 1000))
    
    def _create_error_response(self, query: str, error_message: str, processing_time: int) -> Dict[str, Any]:
        """Create standardized error response.
        
        Args:
            query: Original query
            error_message: Error description
            processing_time: Time spent processing
            
        Returns:
            Error response dictionary
        """
        return {
            'query_id': f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            'query_text': query,
            'response': f"I apologize, but I encountered an error while processing your request: {error_message}. Please try again or contact support if the issue persists.",
            'sources': [],
            'metadata': {
                'processing_time_ms': processing_time,
                'total_sources_considered': 0,
                'confidence_score': 0.0,
                'query_type': 'error',
                'model_used': 'rag_pipeline_error'
            },
            'timestamp': datetime.utcnow().isoformat(),
            'generation_successful': False,
            'error': error_message
        }
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get RAG pipeline statistics.
        
        Returns:
            Dictionary with pipeline statistics
        """
        try:
            # Get retrieval stats
            retrieval_stats = await self.retriever.get_retrieval_stats()
            
            # Get vector store stats (includes query history)
            vector_stats = await self.vector_store.get_stats()
            
            return {
                'pipeline_status': 'healthy',
                'total_reports_available': retrieval_stats.get('total_reports_available', 0),
                'total_queries_processed': vector_stats.get('total_queries', 0),
                'reports_by_ata_chapter': retrieval_stats.get('reports_by_ata_chapter', {}),
                'reports_by_severity': retrieval_stats.get('reports_by_severity', {}),
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return {
                'pipeline_status': 'error',
                'error': str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check RAG pipeline health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Check retriever health
            retriever_health = await self.retriever.health_check()
            
            # Check generator health
            generator_health = self.generator.health_check()
            
            # Check vector store health
            vector_health = await self.vector_store.health_check()
            
            # Determine overall health
            all_healthy = all([
                retriever_health.get('status') == 'healthy',
                generator_health.get('status') == 'healthy',
                vector_health.get('status') == 'healthy'
            ])
            
            return {
                'status': 'healthy' if all_healthy else 'unhealthy',
                'components': {
                    'retriever': retriever_health,
                    'generator': generator_health,
                    'vector_store': vector_health
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"RAG pipeline health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
