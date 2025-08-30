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

# Initialize classification service
classifier_service = ClassifierService()

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
        
        # Process reports with classification system (Phase 3 implementation)
        processed_reports = []
        classification_stats = {"classified": 0, "failed": 0}
        
        for i, report_text in enumerate(reports[:10], 1):  # Limit to 10 reports for demo
            try:
                # Classify the report
                classification = classifier_service.classify_report(
                    report_text, 
                    {"aircraft_type": aircraft_model} if aircraft_model else None
                )
                
                # Get classification summary
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
        
        upload_result = {
            "status": "processed",
            "filename": file.filename,
            "total_reports": len(reports),
            "processed_reports": min(len(reports), 10),  # Limited for demo
            "batch_id": batch_id or f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "aircraft_model": aircraft_model,
            "uploaded_at": datetime.utcnow().isoformat(),
            "classification_stats": classification_stats,
            "sample_results": processed_reports[:3],  # Show first 3 as samples
            "message": f"File processed successfully with Phase 3 classification system. Classified {classification_stats['classified']} reports."
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
        
        # Process report with classification system (Phase 3 implementation)
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
            
            ingestion_result = {
                "status": "ingested_and_classified",
                "report_id": f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                "report_text": report_text[:200] + "..." if len(report_text) > 200 else report_text,
                "aircraft_model": aircraft_model,
                "report_date": report_date or datetime.utcnow().isoformat(),
                "ingested_at": datetime.utcnow().isoformat(),
                "classification": classification_summary,
                "message": "Report ingested and classified successfully using Phase 3 classification system."
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
        
        # TODO: Implement actual database query in later phases
        # For now, return mock response
        mock_reports = [
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
            mock_reports = [r for r in mock_reports if r["ata_chapter"] == ata_chapter]
        if aircraft_model:
            mock_reports = [r for r in mock_reports if aircraft_model.lower() in r["aircraft_model"].lower()]
        if defect_type:
            mock_reports = [r for r in mock_reports if defect_type.lower() in r["defect_type"].lower()]
        
        list_result = {
            "reports": mock_reports,
            "pagination": {
                "page": page,
                "size": size,
                "total": len(mock_reports),
                "pages": 1
            },
            "filters": {
                "ata_chapter": ata_chapter,
                "aircraft_model": aircraft_model,
                "defect_type": defect_type
            },
            "message": "Report listing will be fully implemented in Phase 4 with database integration."
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
        # TODO: Implement actual database query in later phases
        # For now, return mock response
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
            "message": "Report details will be fully implemented in Phase 4 with database integration."
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

@reports_router.get("/stats/summary")
async def get_report_stats() -> Dict[str, Any]:
    """
    Get summary statistics for maintenance reports
    
    Returns counts by ATA chapter, aircraft model, and defect type
    """
    try:
        # TODO: Implement actual statistics calculation in later phases
        # For now, return mock response
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
            "message": "Statistics will be fully implemented in Phase 4 with database integration."
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Statistics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Statistics retrieval failed")

