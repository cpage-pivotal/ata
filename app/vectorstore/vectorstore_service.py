"""Vector store service with CRUD operations and similarity search."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select, func, and_, or_
from sqlalchemy.dialects.postgresql import insert

from .models import MaintenanceReport, QueryHistory, Base
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for vector store operations with pgvector."""
    
    def __init__(self, database_url: str, embedding_service: EmbeddingService):
        """Initialize vector store service.
        
        Args:
            database_url: PostgreSQL connection URL
            embedding_service: Service for generating embeddings
        """
        self.database_url = database_url
        self.embedding_service = embedding_service
        
        # Create async engine
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        # Create session factory
        self.async_session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        logger.info("Initialized VectorStoreService")
    
    async def initialize_database(self):
        """Initialize database tables and extensions."""
        try:
            async with self.engine.begin() as conn:
                # Enable pgvector extension
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                
                # Create tables
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False

    async def store_report(self,
                           report_text: str,
                           classification: Dict[str, Any],
                           aircraft_model: Optional[str] = None,
                           report_date: Optional[datetime] = None) -> Optional[str]:
        """Store a maintenance report with its classification and embedding.

        Args:
            report_text: The maintenance report text
            classification: Classification results from Phase 3
            aircraft_model: Aircraft model (optional)
            report_date: Report date (optional)

        Returns:
            Report ID if successful, None otherwise
        """
        try:
            # Generate embedding
            embedding = await self.embedding_service.generate_embedding_async(report_text)
            if not embedding:
                logger.error("Failed to generate embedding for report")
                return None

            # Extract classification data from nested structure
            # The classification dict has both summary and detailed sections
            ata_data = classification.get('ata', {})
            ispec_data = classification.get('ispec', {})
            defect_data = classification.get('defect', {})

            # Extract ATA chapter info - try different possible keys
            ata_chapter = (
                    ata_data.get('chapter') or
                    classification.get('ata_chapter') or
                    str(ata_data.get('chapter', '')).strip() or
                    None
            )

            ata_chapter_name = (
                    ata_data.get('chapter_name') or
                    classification.get('ata_chapter_name') or
                    None
            )

            # Extract other classification fields
            defect_types = (
                    defect_data.get('defect_types', []) or
                    classification.get('defect_types', [])
            )

            maintenance_actions = (
                    defect_data.get('maintenance_actions', []) or
                    classification.get('maintenance_actions', [])
            )

            identified_parts = (
                    ispec_data.get('identified_parts', []) or
                    classification.get('identified_parts', [])
            )

            severity = (
                    defect_data.get('severity') or
                    classification.get('severity')
            )

            safety_critical = (
                    defect_data.get('safety_critical') or
                    classification.get('safety_critical', False)
            )

            overall_confidence = classification.get('overall_confidence', 0.0)

            # Handle processing_notes - convert list to string if needed
            processing_notes = classification.get('processing_notes', '')
            if isinstance(processing_notes, list):
                processing_notes = '; '.join(str(note) for note in processing_notes)
            elif not isinstance(processing_notes, str):
                processing_notes = str(processing_notes)

            # Handle list fields that should be lists
            if not isinstance(identified_parts, list):
                identified_parts = [str(identified_parts)] if identified_parts else []

            if not isinstance(defect_types, list):
                defect_types = [str(defect_types)] if defect_types else []

            if not isinstance(maintenance_actions, list):
                maintenance_actions = [str(maintenance_actions)] if maintenance_actions else []

            # Handle field length constraints
            if ata_chapter and len(str(ata_chapter)) > 10:
                ata_chapter = str(ata_chapter)[:10]
                logger.warning(f"ATA chapter truncated to 10 chars: {ata_chapter}")

            # Truncate confidence score to 10 characters (e.g., "0.34" instead of "0.33999999999999997")
            confidence_str = f"{float(overall_confidence):.2f}"[:10]

            # Truncate aircraft model if too long (though 100 chars should be enough)
            if aircraft_model and len(aircraft_model) > 100:
                aircraft_model = aircraft_model[:100]
                logger.warning(f"Aircraft model truncated to 100 chars")

            # Debug logging to see what we're actually storing
            logger.info(f"Storing report with ATA: {ata_chapter} ({ata_chapter_name}), Defects: {defect_types}, Severity: {severity}")

            # Create report record
            report = MaintenanceReport(
                report_text=report_text,
                aircraft_model=aircraft_model,
                report_date=report_date,
                ata_chapter=ata_chapter,
                ata_chapter_name=ata_chapter_name,
                ispec_parts=identified_parts,
                defect_types=defect_types,
                maintenance_actions=maintenance_actions,
                severity=severity,
                safety_critical=str(safety_critical).lower()[:10],
                confidence_score=confidence_str,
                embedding=embedding,
                classification_metadata=classification,  # Store full classification JSON
                processing_notes=processing_notes
            )

            async with self.async_session_factory() as session:
                session.add(report)
                await session.commit()
                await session.refresh(report)

                logger.info(f"Stored report with ID: {report.id}")
                return str(report.id)

        except Exception as e:
            logger.error(f"Error storing report: {e}")
            return None

    async def store_reports_batch(self,
                                  reports_data: List[Dict[str, Any]]) -> List[Optional[str]]:
        """Store multiple reports in batch.

        Args:
            reports_data: List of dictionaries with report data and classification

        Returns:
            List of report IDs (None for failed reports)
        """
        try:
            # Extract texts for batch embedding generation
            texts = [data['report_text'] for data in reports_data]

            # Generate embeddings in batch
            embeddings = await self.embedding_service.generate_embeddings_batch_async(texts)

            # Create report records
            reports = []
            report_ids = []

            for i, (data, embedding) in enumerate(zip(reports_data, embeddings)):
                if not embedding:
                    logger.warning(f"Failed to generate embedding for report {i}")
                    report_ids.append(None)
                    continue

                classification = data.get('classification', {})

                # Extract classification data from nested structure
                ata_data = classification.get('ata', {})
                ispec_data = classification.get('ispec', {})
                defect_data = classification.get('defect', {})

                # Extract ATA chapter info - try different possible keys
                ata_chapter = (
                        ata_data.get('chapter') or
                        classification.get('ata_chapter') or
                        str(ata_data.get('chapter', '')).strip() or
                        None
                )

                ata_chapter_name = (
                        ata_data.get('chapter_name') or
                        classification.get('ata_chapter_name') or
                        None
                )

                # Extract other classification fields
                defect_types = (
                        defect_data.get('defect_types', []) or
                        classification.get('defect_types', [])
                )

                maintenance_actions = (
                        defect_data.get('maintenance_actions', []) or
                        classification.get('maintenance_actions', [])
                )

                identified_parts = (
                        ispec_data.get('identified_parts', []) or
                        classification.get('identified_parts', [])
                )

                severity = (
                        defect_data.get('severity') or
                        classification.get('severity')
                )

                safety_critical = (
                        defect_data.get('safety_critical') or
                        classification.get('safety_critical', False)
                )

                overall_confidence = classification.get('overall_confidence', 0.0)

                # Handle processing_notes - convert list to string if needed
                processing_notes = classification.get('processing_notes', '')
                if isinstance(processing_notes, list):
                    processing_notes = '; '.join(str(note) for note in processing_notes)
                elif not isinstance(processing_notes, str):
                    processing_notes = str(processing_notes)

                # Handle list fields that should be lists
                if not isinstance(identified_parts, list):
                    identified_parts = [str(identified_parts)] if identified_parts else []

                if not isinstance(defect_types, list):
                    defect_types = [str(defect_types)] if defect_types else []

                if not isinstance(maintenance_actions, list):
                    maintenance_actions = [str(maintenance_actions)] if maintenance_actions else []

                # Handle field length constraints
                if ata_chapter and len(str(ata_chapter)) > 10:
                    ata_chapter = str(ata_chapter)[:10]
                    logger.warning(f"ATA chapter truncated to 10 chars: {ata_chapter}")

                # Truncate confidence score to 10 characters
                confidence_str = f"{float(overall_confidence):.2f}"[:10]

                # Truncate aircraft model if too long
                aircraft_model = data.get('aircraft_model')
                if aircraft_model and len(aircraft_model) > 100:
                    aircraft_model = aircraft_model[:100]
                    logger.warning(f"Aircraft model truncated to 100 chars")

                # Debug logging
                logger.info(f"Batch storing report {i+1} with ATA: {ata_chapter} ({ata_chapter_name})")

                report = MaintenanceReport(
                    report_text=data['report_text'],
                    aircraft_model=aircraft_model,
                    report_date=data.get('report_date'),
                    ata_chapter=ata_chapter,
                    ata_chapter_name=ata_chapter_name,
                    ispec_parts=identified_parts,
                    defect_types=defect_types,
                    maintenance_actions=maintenance_actions,
                    severity=severity,
                    safety_critical=str(safety_critical).lower()[:10],
                    confidence_score=confidence_str,
                    embedding=embedding,
                    classification_metadata=classification,  # Store full classification JSON
                    processing_notes=processing_notes
                )

                reports.append(report)
                report_ids.append(str(report.id))

            # Bulk insert
            if reports:
                async with self.async_session_factory() as session:
                    session.add_all(reports)
                    await session.commit()

                logger.info(f"Stored {len(reports)} reports in batch")

            return report_ids

        except Exception as e:
            logger.error(f"Error storing reports batch: {e}")
            return [None] * len(reports_data)

    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a report by ID.
        
        Args:
            report_id: Report UUID
            
        Returns:
            Report data dictionary or None
        """
        try:
            async with self.async_session_factory() as session:
                report = await session.get(MaintenanceReport, uuid.UUID(report_id))
                if report:
                    return report.to_dict()
                return None
                
        except Exception as e:
            logger.error(f"Error getting report {report_id}: {e}")
            return None
    
    async def list_reports(self, 
                          skip: int = 0, 
                          limit: int = 100,
                          ata_chapter: Optional[str] = None,
                          severity: Optional[str] = None,
                          defect_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List reports with optional filtering.
        
        Args:
            skip: Number of reports to skip
            limit: Maximum number of reports to return
            ata_chapter: Filter by ATA chapter
            severity: Filter by severity level
            defect_type: Filter by defect type
            
        Returns:
            List of report dictionaries
        """
        try:
            async with self.async_session_factory() as session:
                query = select(MaintenanceReport)
                
                # Apply filters
                filters = []
                if ata_chapter:
                    filters.append(MaintenanceReport.ata_chapter == ata_chapter)
                if severity:
                    filters.append(MaintenanceReport.severity == severity)
                if defect_type:
                    filters.append(MaintenanceReport.defect_types.contains([defect_type]))
                
                if filters:
                    query = query.where(and_(*filters))
                
                # Order by creation date (newest first)
                query = query.order_by(MaintenanceReport.created_at.desc())
                query = query.offset(skip).limit(limit)
                
                result = await session.execute(query)
                reports = result.scalars().all()
                
                return [report.to_dict() for report in reports]
                
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            return []
    
    async def similarity_search(self, 
                               query_text: str, 
                               limit: int = 10,
                               similarity_threshold: float = 0.5,
                               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform vector similarity search.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)
            filters: Optional filters (ata_chapter, severity, etc.)
            
        Returns:
            List of reports with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding_async(query_text)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            async with self.async_session_factory() as session:
                # Build similarity query
                similarity_expr = MaintenanceReport.embedding.cosine_distance(query_embedding)
                
                query = select(
                    MaintenanceReport,
                    (1 - similarity_expr).label('similarity_score')
                )
                
                # Apply filters
                filter_conditions = []
                if filters:
                    if filters.get('ata_chapter'):
                        filter_conditions.append(MaintenanceReport.ata_chapter == filters['ata_chapter'])
                    if filters.get('severity'):
                        filter_conditions.append(MaintenanceReport.severity == filters['severity'])
                    if filters.get('defect_type'):
                        filter_conditions.append(MaintenanceReport.defect_types.contains([filters['defect_type']]))
                    if filters.get('aircraft_model'):
                        filter_conditions.append(MaintenanceReport.aircraft_model == filters['aircraft_model'])
                
                if filter_conditions:
                    query = query.where(and_(*filter_conditions))
                
                # Apply similarity threshold and ordering
                query = query.where((1 - similarity_expr) >= similarity_threshold)
                query = query.order_by(similarity_expr.asc())  # Ascending distance = descending similarity
                query = query.limit(limit)
                
                result = await session.execute(query)
                rows = result.all()
                
                # Format results
                results = []
                for report, similarity_score in rows:
                    report_dict = report.to_dict()
                    report_dict['similarity_score'] = float(similarity_score)
                    results.append(report_dict)
                
                logger.info(f"Found {len(results)} similar reports for query: {query_text[:50]}...")
                return results
                
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    async def store_query(self, 
                         query_text: str,
                         response_text: str,
                         sources: List[Dict[str, Any]],
                         processing_time_ms: int,
                         query_type: str = "natural_language") -> Optional[str]:
        """Store a query and its response for history tracking.
        
        Args:
            query_text: Original query
            response_text: Generated response
            sources: List of source reports used
            processing_time_ms: Processing time in milliseconds
            query_type: Type of query
            
        Returns:
            Query ID if successful
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding_async(query_text)
            
            query_record = QueryHistory(
                query_text=query_text,
                query_embedding=query_embedding,
                response_text=response_text,
                sources=sources,
                query_type=query_type,
                processing_time_ms=str(processing_time_ms)
            )
            
            async with self.async_session_factory() as session:
                session.add(query_record)
                await session.commit()
                await session.refresh(query_record)
                
                logger.info(f"Stored query with ID: {query_record.id}")
                return str(query_record.id)
                
        except Exception as e:
            logger.error(f"Error storing query: {e}")
            return None
    
    async def get_query_history(self, 
                               skip: int = 0, 
                               limit: int = 50) -> List[Dict[str, Any]]:
        """Get query history.
        
        Args:
            skip: Number of queries to skip
            limit: Maximum number of queries to return
            
        Returns:
            List of query dictionaries
        """
        try:
            async with self.async_session_factory() as session:
                query = select(QueryHistory).order_by(QueryHistory.created_at.desc())
                query = query.offset(skip).limit(limit)
                
                result = await session.execute(query)
                queries = result.scalars().all()
                
                return [query.to_dict() for query in queries]
                
        except Exception as e:
            logger.error(f"Error getting query history: {e}")
            return []
    
    async def update_query_feedback(self, 
                                   query_id: str, 
                                   rating: int, 
                                   feedback_text: str = "") -> bool:
        """Update query feedback.
        
        Args:
            query_id: Query UUID
            rating: Feedback rating (1-5)
            feedback_text: Optional feedback text
            
        Returns:
            True if successful
        """
        try:
            async with self.async_session_factory() as session:
                query = await session.get(QueryHistory, uuid.UUID(query_id))
                if query:
                    query.feedback_rating = str(rating)
                    query.feedback_text = feedback_text
                    await session.commit()
                    
                    logger.info(f"Updated feedback for query {query_id}")
                    return True
                    
                return False
                
        except Exception as e:
            logger.error(f"Error updating query feedback: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            async with self.async_session_factory() as session:
                # Count total reports
                total_reports = await session.scalar(select(func.count(MaintenanceReport.id)))
                
                # Count by ATA chapter
                ata_counts = await session.execute(
                    select(MaintenanceReport.ata_chapter, func.count())
                    .group_by(MaintenanceReport.ata_chapter)
                    .order_by(func.count().desc())
                )
                
                # Count by severity
                severity_counts = await session.execute(
                    select(MaintenanceReport.severity, func.count())
                    .group_by(MaintenanceReport.severity)
                    .order_by(func.count().desc())
                )
                
                # Count total queries
                total_queries = await session.scalar(select(func.count(QueryHistory.id)))
                
                return {
                    'total_reports': total_reports or 0,
                    'total_queries': total_queries or 0,
                    'reports_by_ata_chapter': dict(ata_counts.all()),
                    'reports_by_severity': dict(severity_counts.all())
                }
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check vector store health.
        
        Returns:
            Health status dictionary
        """
        try:
            async with self.async_session_factory() as session:
                # Test database connection
                await session.execute(text("SELECT 1"))
                
                # Test vector extension
                await session.execute(text("SELECT vector_dims(ARRAY[1,2,3]::vector)"))
                
                # Get basic stats
                total_reports = await session.scalar(select(func.count(MaintenanceReport.id)))
                
                return {
                    'status': 'healthy',
                    'database_connection': 'ok',
                    'vector_extension': 'ok',
                    'total_reports': total_reports or 0,
                    'embedding_service': self.embedding_service.health_check()
                }
                
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_connection': 'error',
                'vector_extension': 'unknown'
            }
    
    async def close(self):
        """Close database connections."""
        try:
            await self.engine.dispose()
            logger.info("Vector store connections closed")
        except Exception as e:
            logger.error(f"Error closing vector store: {e}")