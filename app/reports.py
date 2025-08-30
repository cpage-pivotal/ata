"""
Reports router for Boeing Aircraft Maintenance Report System
Handles maintenance report upload, ingestion, and retrieval
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import io

# Classification system imports - Phase 3 implementation
from app.classification import ClassifierService

# Vector store imports - Phase 4 implementation
from app.vectorstore import VectorStoreService, EmbeddingService
from app.config import get_settings

# Initialize services
classifier_service = ClassifierService()

# Global variables for services (will be initialized in main.py)
vector_store_service: Optional[VectorStoreService] = None

def set_vector_store_service(service: VectorStoreService):
    """Set the vector store service (called from main.py)"""
    global vector_store_service
    vector_store_service = service

logger = logging.getLogger(__name__)
reports_router = APIRouter()

@reports_router.post("/upload")
async def upload_reports(
    file: UploadFile = File(...),
    aircraft_model: Optional[str] = Form(None),
    batch_id: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Upload maintenance reports file for batch processing
    
    Accepts text files with one maintenance report per line
    Returns upload status and processing information
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.txt', '.csv')):
            raise HTTPException(
                status_code=400, 
                detail="Only .txt and .csv files are supported"
            )
        
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Split into individual reports (one per line)
        reports = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        if not reports:
            raise HTTPException(
                status_code=400,
                detail="File contains no valid reports"
            )
        
        # Process reports with classification and storage (Phase 3 + 4 implementation)
        processed_reports = []
        classification_stats = {"classified": 0, "failed": 0, "stored": 0}
        stored_report_ids = []
        
        # Prepare data for batch processing
        reports_data = []
        
        for i, report_text in enumerate(reports[:10], 1):  # Limit to 10 reports for demo
            try:
                # Classify the report
                classification = classifier_service.classify_report(
                    report_text, 
                    {"aircraft_type": aircraft_model} if aircraft_model else None
                )
                
                # Prepare data for storage
                reports_data.append({
                    "report_text": report_text,
                    "aircraft_model": aircraft_model,
                    "report_date": datetime.utcnow(),
                    "classification": classifier_service.to_dict(classification)
                })
                
                # Get classification summary for response
                summary = classifier_service.get_classification_summary(classification)
                
                processed_reports.append({
                    "report_number": i,
                    "report_text": report_text[:100] + "..." if len(report_text) > 100 else report_text,
                    "classification": summary
                })
                
                classification_stats["classified"] += 1
                
            except Exception as e:
                logger.error(f"Failed to classify report {i}: {e}")
                processed_reports.append({
                    "report_number": i,
                    "report_text": report_text[:100] + "..." if len(report_text) > 100 else report_text,
                    "classification": {"error": f"Classification failed: {str(e)}"}
                })
                classification_stats["failed"] += 1
        
        # Store reports in vector database if available
        if vector_store_service and reports_data:
            try:
                stored_report_ids = await vector_store_service.store_reports_batch(reports_data)
                classification_stats["stored"] = len([id for id in stored_report_ids if id is not None])
                logger.info(f"Stored {classification_stats['stored']} reports in vector database")
            except Exception as e:
                logger.error(f"Failed to store reports in vector database: {e}")
                classification_stats["storage_error"] = str(e)
        
        upload_result = {
            "status": "processed_and_stored" if vector_store_service and classification_stats.get("stored", 0) > 0 else "processed",
            "filename": file.filename,
            "total_reports": len(reports),
            "processed_reports": min(len(reports), 10),  # Limited for demo
            "batch_id": batch_id or f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "aircraft_model": aircraft_model,
            "uploaded_at": datetime.utcnow().isoformat(),
            "classification_stats": classification_stats,
            "stored_report_ids": stored_report_ids if stored_report_ids else [],
            "sample_results": processed_reports[:3],  # Show first 3 as samples
            "message": f"File processed with Phase 3+4 system. Classified {classification_stats['classified']} reports, stored {classification_stats.get('stored', 0)} in vector database." if vector_store_service else f"File processed with Phase 3 classification system. Classified {classification_stats['classified']} reports. Vector storage not available."
        }
        
        logger.info(f"File uploaded: {file.filename} with {len(reports)} reports")
        
        return upload_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@reports_router.post("/ingest")
async def ingest_single_report(
    report_text: str = Form(...),
    aircraft_model: Optional[str] = Form(None),
    report_date: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Ingest a single maintenance report
    
    Accepts individual report text and metadata
    Returns ingestion status and classification results
    """
    try:
        if not report_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Report text cannot be empty"
            )
        
        # Process report with classification and storage (Phase 3 + 4 implementation)
        try:
            # Classify the report
            classification = classifier_service.classify_report(
                report_text, 
                {
                    "aircraft_type": aircraft_model,
                    "report_date": report_date
                } if aircraft_model or report_date else None
            )
            
            # Get classification summary
            classification_summary = classifier_service.get_classification_summary(classification)
            classification_dict = classifier_service.to_dict(classification)
            
            # Store in vector database if available
            report_id = None
            if vector_store_service:
                try:
                    parsed_date = None
                    if report_date:
                        try:
                            parsed_date = datetime.fromisoformat(report_date.replace('Z', '+00:00'))
                        except ValueError:
                            parsed_date = datetime.utcnow()
                    else:
                        parsed_date = datetime.utcnow()
                    
                    report_id = await vector_store_service.store_report(
                        report_text=report_text,
                        classification=classification_dict,
                        aircraft_model=aircraft_model,
                        report_date=parsed_date
                    )
                except Exception as storage_error:
                    logger.error(f"Failed to store report in vector database: {storage_error}")
                    report_id = None
            
            # Generate fallback ID if storage failed or unavailable
            if not report_id:
                report_id = f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            
            ingestion_result = {
                "status": "ingested_classified_and_stored" if vector_store_service and report_id else "ingested_and_classified",
                "report_id": report_id,
                "report_text": report_text[:200] + "..." if len(report_text) > 200 else report_text,
                "aircraft_model": aircraft_model,
                "report_date": report_date or datetime.utcnow().isoformat(),
                "ingested_at": datetime.utcnow().isoformat(),
                "classification": classification_summary,
                "message": "Report ingested, classified, and stored successfully using Phase 3+4 system." if vector_store_service and report_id else "Report ingested and classified successfully. Vector storage not available."
            }
            
        except Exception as classification_error:
            logger.error(f"Classification failed for single report: {classification_error}")
            ingestion_result = {
                "status": "ingested_with_classification_error",
                "report_id": f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                "report_text": report_text[:200] + "..." if len(report_text) > 200 else report_text,
                "aircraft_model": aircraft_model,
                "report_date": report_date or datetime.utcnow().isoformat(),
                "ingested_at": datetime.utcnow().isoformat(),
                "classification_error": str(classification_error),
                "message": "Report ingested but classification failed. Manual review may be required."
            }
        
        logger.info(f"Single report ingested: {ingestion_result['report_id']}")
        
        return ingestion_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="Report ingestion failed")

@reports_router.get("/")
async def list_reports(
    page: int = 1,
    size: int = 20,
    ata_chapter: Optional[str] = None,
    aircraft_model: Optional[str] = None,
    defect_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    List maintenance reports with pagination and filtering
    
    Supports filtering by ATA chapter, aircraft model, and defect type
    Returns paginated results with metadata
    """
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 20
        
        # Use vector store if available, otherwise fall back to mock data
        reports = []
        total_reports = 0
        
        if vector_store_service:
            try:
                # Calculate skip for pagination
                skip = (page - 1) * size
                
                # Build filters
                filters = {}
                if ata_chapter:
                    filters['ata_chapter'] = ata_chapter
                if defect_type:
                    filters['defect_type'] = defect_type
                
                # Get reports from vector store
                reports = await vector_store_service.list_reports(
                    skip=skip,
                    limit=size,
                    ata_chapter=ata_chapter,
                    defect_type=defect_type
                )
                
                # Get total count for pagination (simplified - using current batch size)
                total_reports = len(reports) + skip  # Approximation
                
            except Exception as e:
                logger.error(f"Failed to list reports from vector store: {e}")
                reports = []
                total_reports = 0
        
        # Fall back to mock data if vector store unavailable or no results
        if not reports and not vector_store_service:
            reports = [
                {
                    "id": f"report_{i}",
                    "report_text": f"Sample maintenance report {i}",
                    "aircraft_model": "Boeing 737-800",
                    "report_date": "2024-01-15T10:00:00Z",
                    "ata_chapter": "32",
                    "ispec_part": "Landing Gear",
                    "defect_type": "corrosion",
                    "created_at": "2024-01-15T10:00:00Z"
                }
                for i in range(1, min(size + 1, 6))  # Mock 5 reports max
            ]
            
            # Apply filters (mock implementation)
            if ata_chapter:
                reports = [r for r in reports if r["ata_chapter"] == ata_chapter]
            if aircraft_model:
                reports = [r for r in reports if aircraft_model.lower() in r["aircraft_model"].lower()]
            if defect_type:
                reports = [r for r in reports if defect_type.lower() in r["defect_type"].lower()]
            
            total_reports = len(reports)
        
        pages = max(1, (total_reports + size - 1) // size)  # Ceiling division
        
        list_result = {
            "reports": reports,
            "pagination": {
                "page": page,
                "size": size,
                "total": total_reports,
                "pages": pages
            },
            "filters": {
                "ata_chapter": ata_chapter,
                "aircraft_model": aircraft_model,
                "defect_type": defect_type
            },
            "message": "Reports retrieved from vector database (Phase 4)" if vector_store_service and reports else "Using mock data - vector database not available"
        }
        
        return list_result
        
    except Exception as e:
        logger.error(f"Report listing failed: {e}")
        raise HTTPException(status_code=500, detail="Report listing failed")

@reports_router.get("/{report_id}")
async def get_report(report_id: str) -> Dict[str, Any]:
    """
    Get a specific maintenance report by ID
    
    Returns full report details including classification and metadata
    """
    try:
        # Use vector store if available, otherwise fall back to mock data
        if vector_store_service:
            try:
                report = await vector_store_service.get_report(report_id)
                if report:
                    return report
            except Exception as e:
                logger.error(f"Failed to get report from vector store: {e}")
        
        # Fall back to mock response if vector store unavailable or report not found
        if not report_id.startswith("report_"):
            raise HTTPException(status_code=404, detail="Report not found")
        
        mock_report = {
            "id": report_id,
            "report_text": "Sample maintenance report with detailed information about hydraulic leak at nose gear actuator. B-nut connection showing signs of corrosion. Replaced seal and torqued to specification.",
            "aircraft_model": "Boeing 737-800",
            "report_date": "2024-01-15T10:00:00Z",
            "ata_chapter": "32",
            "ispec_part": "Landing Gear",
            "defect_type": "corrosion",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z",
            "message": "Using mock data - vector database not available or report not found"
        }
        
        return mock_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Report retrieval failed")

@reports_router.post("/classify")
async def classify_report_text(
    report_text: str = Form(...),
    aircraft_model: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Classify a maintenance report without storing it
    
    Useful for testing the classification system or getting classification
    results before deciding whether to ingest a report
    """
    try:
        if not report_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Report text cannot be empty"
            )
        
        # Classify the report
        classification = classifier_service.classify_report(
            report_text, 
            {"aircraft_type": aircraft_model} if aircraft_model else None
        )
        
        # Get detailed classification results
        classification_dict = classifier_service.to_dict(classification)
        summary = classifier_service.get_classification_summary(classification)
        
        return {
            "status": "classified",
            "report_text": report_text[:200] + "..." if len(report_text) > 200 else report_text,
            "aircraft_model": aircraft_model,
            "classification_summary": summary,
            "detailed_classification": classification_dict,
            "classified_at": datetime.utcnow().isoformat(),
            "message": "Report classified successfully using Phase 3 classification system."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report classification failed: {e}")
        raise HTTPException(status_code=500, detail="Report classification failed")

@reports_router.get("/classification/health")
async def get_classification_health() -> Dict[str, Any]:
    """
    Get health status of the classification system
    
    Returns status of all classification components
    """
    try:
        health_status = classifier_service.get_health_status()
        return health_status
        
    except Exception as e:
        logger.error(f"Classification health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Classification system health check failed"
        }

@reports_router.post("/search")
async def search_reports(
    query: str = Form(...),
    limit: int = Form(10),
    similarity_threshold: float = Form(0.5),
    ata_chapter: Optional[str] = Form(None),
    severity: Optional[str] = Form(None),
    defect_type: Optional[str] = Form(None),
    aircraft_model: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Search maintenance reports using semantic similarity
    
    Performs vector similarity search to find relevant reports
    based on natural language queries
    """
    try:
        if not query.strip():
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty"
            )
        
        # Use vector store if available
        if vector_store_service:
            try:
                # Build filters
                filters = {}
                if ata_chapter:
                    filters['ata_chapter'] = ata_chapter
                if severity:
                    filters['severity'] = severity
                if defect_type:
                    filters['defect_type'] = defect_type
                if aircraft_model:
                    filters['aircraft_model'] = aircraft_model
                
                # Perform similarity search
                results = await vector_store_service.similarity_search(
                    query_text=query,
                    limit=min(limit, 50),  # Cap at 50 results
                    similarity_threshold=max(0.0, min(1.0, similarity_threshold)),  # Clamp to 0-1
                    filters=filters if any(filters.values()) else None
                )
                
                return {
                    "status": "search_completed",
                    "query": query,
                    "filters": filters,
                    "results_count": len(results),
                    "similarity_threshold": similarity_threshold,
                    "results": results,
                    "message": f"Found {len(results)} similar reports using Phase 4 vector search"
                }
                
            except Exception as e:
                logger.error(f"Vector similarity search failed: {e}")
                raise HTTPException(status_code=500, detail="Similarity search failed")
        
        else:
            # Return mock response when vector store not available
            return {
                "status": "search_unavailable",
                "query": query,
                "results_count": 0,
                "results": [],
                "message": "Similarity search requires vector database (Phase 4). Currently running in Phase 3 mode."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search operation failed")

@reports_router.get("/vectorstore/health")
async def get_vectorstore_health() -> Dict[str, Any]:
    """
    Get health status of the vector store system
    
    Returns status of vector database, embedding service, and related components
    """
    try:
        if vector_store_service:
            health_status = await vector_store_service.health_check()
            health_status["phase"] = "Phase 4 - Vector Store Active"
            return health_status
        else:
            return {
                "status": "unavailable",
                "phase": "Phase 3 - Classification Only",
                "message": "Vector store service not initialized. Running in classification-only mode.",
                "database_connection": "not_configured",
                "vector_extension": "not_available",
                "embedding_service": {"status": "not_configured"}
            }
        
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Vector store health check failed"
        }

@reports_router.get("/stats/summary")
async def get_report_stats() -> Dict[str, Any]:
    """
    Get summary statistics for maintenance reports
    
    Returns counts by ATA chapter, aircraft model, and defect type
    """
    try:
        # Use vector store if available, otherwise fall back to mock data
        if vector_store_service:
            try:
                stats = await vector_store_service.get_stats()
                stats["last_updated"] = datetime.utcnow().isoformat()
                stats["message"] = "Statistics retrieved from vector database (Phase 4)"
            except Exception as e:
                logger.error(f"Failed to get stats from vector store: {e}")
                # Fall back to mock stats
                stats = {
                    "total_reports": 0,
                    "by_ata_chapter": {},
                    "by_aircraft_model": {},
                    "by_defect_type": {},
                    "last_updated": datetime.utcnow().isoformat(),
                    "message": "Using mock data - vector database not available"
                }
        else:
            # Mock response when vector store not available
            stats = {
                "total_reports": 0,
                "by_ata_chapter": {
                    "32": 0,  # Landing Gear
                    "27": 0,  # Flight Controls
                    "21": 0,  # Air Conditioning
                    "53": 0   # Fuselage
                },
                "by_aircraft_model": {
                    "Boeing 737-800": 0,
                    "Boeing 737-900": 0,
                    "Boeing 787": 0
                },
                "by_defect_type": {
                    "corrosion": 0,
                    "crack": 0,
                    "leak": 0,
                    "wear": 0
                },
                "last_updated": datetime.utcnow().isoformat(),
                "message": "Using mock data - vector database not available"
            }
        
        return stats
        
    except Exception as e:
        logger.error(f"Statistics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Statistics retrieval failed")

