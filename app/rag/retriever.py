"""Retrieval component for RAG pipeline - finds relevant maintenance reports."""

import logging
from typing import List, Dict, Any, Optional
from ..vectorstore.vectorstore_service import VectorStoreService

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieval component for finding relevant maintenance reports."""
    
    def __init__(self, vector_store: VectorStoreService):
        """Initialize retriever.
        
        Args:
            vector_store: Vector store service for similarity search
        """
        self.vector_store = vector_store
        logger.info("Initialized Retriever")
    
    async def retrieve_relevant_reports(self, 
                                      query: str,
                                      max_results: int = 10,
                                      similarity_threshold: float = 0.3,
                                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve maintenance reports relevant to the query.
        
        Args:
            query: User's question or search query
            max_results: Maximum number of reports to retrieve
            similarity_threshold: Minimum similarity score (0-1)
            filters: Optional filters (ata_chapter, severity, etc.)
            
        Returns:
            List of relevant maintenance reports with similarity scores
        """
        try:
            logger.info(f"Retrieving reports for query: '{query[:50]}...'")
            
            # Perform vector similarity search
            reports = await self.vector_store.similarity_search(
                query_text=query,
                limit=max_results,
                similarity_threshold=similarity_threshold,
                filters=filters
            )
            
            if not reports:
                logger.warning(f"No reports found for query: {query}")
                return []
            
            # Enhance reports with additional context
            enhanced_reports = await self._enhance_reports(reports)
            
            logger.info(f"Retrieved {len(enhanced_reports)} relevant reports")
            return enhanced_reports
            
        except Exception as e:
            logger.error(f"Error retrieving reports: {e}")
            return []
    
    async def retrieve_by_ata_chapter(self, 
                                    query: str,
                                    ata_chapter: str,
                                    max_results: int = 10,
                                    similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Retrieve reports filtered by specific ATA chapter.
        
        Args:
            query: User's question
            ata_chapter: ATA chapter to filter by
            max_results: Maximum number of reports
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of relevant reports from the specified ATA chapter
        """
        filters = {'ata_chapter': ata_chapter}
        
        return await self.retrieve_relevant_reports(
            query=query,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            filters=filters
        )
    
    async def retrieve_by_defect_type(self, 
                                    query: str,
                                    defect_type: str,
                                    max_results: int = 10,
                                    similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Retrieve reports filtered by defect type.
        
        Args:
            query: User's question
            defect_type: Defect type to filter by
            max_results: Maximum number of reports
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of relevant reports with the specified defect type
        """
        filters = {'defect_type': defect_type}
        
        return await self.retrieve_relevant_reports(
            query=query,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            filters=filters
        )
    
    async def retrieve_safety_critical(self, 
                                     query: str,
                                     max_results: int = 15,
                                     similarity_threshold: float = 0.4) -> List[Dict[str, Any]]:
        """Retrieve safety-critical maintenance reports.
        
        Args:
            query: User's safety-related question
            max_results: Maximum number of reports
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of safety-critical reports relevant to the query
        """
        try:
            # First, get all relevant reports
            all_reports = await self.retrieve_relevant_reports(
                query=query,
                max_results=max_results * 2,  # Get more to filter from
                similarity_threshold=similarity_threshold
            )
            
            # Filter for safety-critical reports
            safety_critical_reports = [
                report for report in all_reports
                if report.get('safety_critical', 'false').lower() == 'true'
            ]
            
            # If we don't have enough safety-critical reports, include high-severity ones
            if len(safety_critical_reports) < max_results:
                high_severity_reports = [
                    report for report in all_reports
                    if report.get('severity', '').lower() in ['major', 'critical']
                    and report not in safety_critical_reports
                ]
                
                safety_critical_reports.extend(high_severity_reports)
            
            # Return up to max_results
            result = safety_critical_reports[:max_results]
            
            logger.info(f"Retrieved {len(result)} safety-critical reports")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving safety-critical reports: {e}")
            return []
    
    async def retrieve_for_trend_analysis(self, 
                                        query: str,
                                        max_results: int = 20,
                                        similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Retrieve reports for trend analysis queries.
        
        Args:
            query: User's trend analysis question
            max_results: Maximum number of reports (higher for trend analysis)
            similarity_threshold: Lower threshold to get more data points
            
        Returns:
            List of reports suitable for trend analysis
        """
        try:
            # Get more reports with lower threshold for trend analysis
            reports = await self.retrieve_relevant_reports(
                query=query,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            # Sort by creation date for temporal analysis
            reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            logger.info(f"Retrieved {len(reports)} reports for trend analysis")
            return reports
            
        except Exception as e:
            logger.error(f"Error retrieving reports for trend analysis: {e}")
            return []
    
    async def _enhance_reports(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance retrieved reports with additional context.
        
        Args:
            reports: List of basic report dictionaries
            
        Returns:
            List of enhanced report dictionaries
        """
        enhanced_reports = []
        
        for report in reports:
            try:
                # Add computed fields
                enhanced_report = report.copy()
                
                # Calculate relevance category based on similarity score
                similarity_score = report.get('similarity_score', 0.0)
                if similarity_score >= 0.8:
                    enhanced_report['relevance_category'] = 'high'
                elif similarity_score >= 0.6:
                    enhanced_report['relevance_category'] = 'medium'
                else:
                    enhanced_report['relevance_category'] = 'low'
                
                # Add safety priority flag
                safety_critical = report.get('safety_critical', 'false').lower() == 'true'
                severity = report.get('severity', '').lower()
                
                if safety_critical or severity in ['critical', 'major']:
                    enhanced_report['safety_priority'] = 'high'
                elif severity == 'moderate':
                    enhanced_report['safety_priority'] = 'medium'
                else:
                    enhanced_report['safety_priority'] = 'low'
                
                # Add defect summary
                defect_types = report.get('defect_types', [])
                if defect_types:
                    enhanced_report['defect_summary'] = ', '.join(defect_types)
                else:
                    enhanced_report['defect_summary'] = 'No specific defects identified'
                
                enhanced_reports.append(enhanced_report)
                
            except Exception as e:
                logger.warning(f"Error enhancing report {report.get('id', 'unknown')}: {e}")
                enhanced_reports.append(report)  # Use original if enhancement fails
        
        return enhanced_reports
    
    async def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about retrieval performance.
        
        Returns:
            Dictionary with retrieval statistics
        """
        try:
            # Get vector store stats
            vector_stats = await self.vector_store.get_stats()
            
            return {
                'total_reports_available': vector_stats.get('total_reports', 0),
                'reports_by_ata_chapter': vector_stats.get('reports_by_ata_chapter', {}),
                'reports_by_severity': vector_stats.get('reports_by_severity', {}),
                'retrieval_service_status': 'healthy'
            }
            
        except Exception as e:
            logger.error(f"Error getting retrieval stats: {e}")
            return {
                'retrieval_service_status': 'error',
                'error': str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check retriever health.
        
        Returns:
            Health status dictionary
        """
        try:
            # Test vector store connectivity
            vector_health = await self.vector_store.health_check()
            
            # Test a simple retrieval
            test_reports = await self.retrieve_relevant_reports(
                query="test query",
                max_results=1,
                similarity_threshold=0.0
            )
            
            return {
                'status': 'healthy',
                'vector_store_status': vector_health.get('status', 'unknown'),
                'test_retrieval': 'ok' if isinstance(test_reports, list) else 'failed'
            }
            
        except Exception as e:
            logger.error(f"Retriever health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

