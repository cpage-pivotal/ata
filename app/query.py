"""
Query router for Boeing Aircraft Maintenance Report System
Handles natural language queries and RAG-powered responses
"""

from fastapi import APIRouter, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

# RAG pipeline imports - Phase 5 implementation
from app.rag.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)
query_router = APIRouter()

# Global RAG pipeline instance (set during startup)
_rag_pipeline: Optional[RAGPipeline] = None

def set_rag_pipeline(rag_pipeline: RAGPipeline):
    """Set the RAG pipeline instance (called from main.py startup)"""
    global _rag_pipeline
    _rag_pipeline = rag_pipeline
    logger.info("RAG pipeline set in query module")

def get_rag_pipeline() -> Optional[RAGPipeline]:
    """Get the current RAG pipeline instance"""
    return _rag_pipeline

@query_router.post("/query")
async def process_query(
    query_text: str = Form(...),
    max_results: Optional[int] = Form(10),
    include_sources: Optional[bool] = Form(True),
    similarity_threshold: Optional[float] = Form(0.5),
    temperature: Optional[float] = Form(0.7),
    ata_chapter: Optional[str] = Form(None),
    query_type: Optional[str] = Form("auto")
) -> Dict[str, Any]:
    """
    Process natural language query using RAG pipeline
    
    Accepts natural language questions about maintenance reports
    Returns AI-generated response with source citations
    """
    try:
        if not query_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Query text cannot be empty"
            )
        
        # Validate parameters
        if max_results and (max_results < 1 or max_results > 50):
            max_results = 10
        if similarity_threshold and (similarity_threshold < 0.0 or similarity_threshold > 1.0):
            similarity_threshold = 0.5
        if temperature and (temperature < 0.0 or temperature > 2.0):
            temperature = 0.7
        
        # Get RAG pipeline
        rag_pipeline = get_rag_pipeline()
        
        if not rag_pipeline:
            # Fallback to mock response if RAG pipeline not available
            logger.warning("RAG pipeline not available, returning mock response")
            return _create_mock_response(query_text, include_sources)
        
        # Process query based on type
        if query_type == "safety" or any(keyword in query_text.lower() for keyword in ['safety', 'critical', 'emergency', 'dangerous']):
            query_result = await rag_pipeline.process_safety_critical_query(
                query=query_text,
                max_results=max_results or 15,
                similarity_threshold=similarity_threshold or 0.4
            )
        elif query_type == "trend" or any(keyword in query_text.lower() for keyword in ['trend', 'pattern', 'recurring', 'frequent']):
            query_result = await rag_pipeline.process_trend_analysis_query(
                query=query_text,
                max_results=max_results or 20,
                similarity_threshold=similarity_threshold or 0.3
            )
        elif ata_chapter:
            query_result = await rag_pipeline.process_ata_specific_query(
                query=query_text,
                ata_chapter=ata_chapter,
                max_results=max_results or 10,
                similarity_threshold=similarity_threshold or 0.3
            )
        else:
            # Standard RAG query
            filters = {}
            if ata_chapter:
                filters['ata_chapter'] = ata_chapter
                
            query_result = await rag_pipeline.process_query(
                query=query_text,
                max_results=max_results or 10,
                similarity_threshold=similarity_threshold or 0.5,
                temperature=temperature or 0.7,
                filters=filters if filters else None
            )
        
        # Filter sources if requested
        if not include_sources:
            query_result['sources'] = []
        
        logger.info(f"RAG query processed: {query_result.get('query_id', 'unknown')} - '{query_text[:50]}...'")
        
        return query_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail="Query processing failed")

def _create_mock_response(query_text: str, include_sources: bool) -> Dict[str, Any]:
    """Create a mock response when RAG pipeline is not available"""
    return {
        "query_id": f"mock_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
        "query_text": query_text,
        "response": f"This is a mock response to your query: '{query_text}'. The RAG pipeline is not currently available. Please ensure the system is properly configured with database and GenAI credentials.",
        "sources": [
            {
                "report_id": "sample_report_1",
                "aircraft_model": "Boeing 737-800",
                "ata_chapter": "32",
                "relevance_score": 0.95,
                "excerpt": "Sample maintenance report about landing gear issues..."
            }
        ] if include_sources else [],
        "metadata": {
            "processing_time_ms": 50,
            "total_sources_considered": 0,
            "confidence_score": 0.0,
            "model_used": "mock_model",
            "query_type": "mock"
        },
        "timestamp": datetime.utcnow().isoformat(),
        "generation_successful": False,
        "message": "RAG pipeline not available - mock response provided."
    }

@query_router.get("/history")
async def get_query_history(
    page: int = 1,
    size: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get query history with pagination and date filtering
    
    Returns list of previous queries with responses and metadata
    """
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if size < 1 or size > 100:
            size = 20
        
        # Get RAG pipeline
        rag_pipeline = get_rag_pipeline()
        
        if rag_pipeline and hasattr(rag_pipeline, 'vector_store'):
            try:
                # Calculate skip offset
                skip = (page - 1) * size
                
                # Get query history from vector store
                queries = await rag_pipeline.vector_store.get_query_history(
                    skip=skip,
                    limit=size
                )
                
                # Format queries for response
                formatted_queries = []
                for query in queries:
                    formatted_query = {
                        "id": query.get('id', 'unknown'),
                        "query_text": query.get('query_text', ''),
                        "response": query.get('response_text', '')[:200] + "..." if len(query.get('response_text', '')) > 200 else query.get('response_text', ''),
                        "timestamp": query.get('created_at', ''),
                        "processing_time_ms": int(query.get('processing_time_ms', '0') or '0'),
                        "sources_count": len(query.get('sources', [])),
                        "query_type": query.get('query_type', 'general')
                    }
                    formatted_queries.append(formatted_query)
                
                # Get total count for pagination (approximate)
                total_queries = len(queries)  # This is just the current page, but good enough for now
                total_pages = max(1, (total_queries + size - 1) // size)
                
                history_result = {
                    "queries": formatted_queries,
                    "pagination": {
                        "page": page,
                        "size": size,
                        "total": total_queries,
                        "pages": total_pages
                    },
                    "filters": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "message": "Query history retrieved from RAG pipeline database."
                }
                
                return history_result
                
            except Exception as e:
                logger.error(f"Error retrieving query history from database: {e}")
                # Fall through to mock response
        
        # Fallback to mock response
        mock_queries = [
            {
                "id": f"mock_query_{i}",
                "query_text": f"Sample query {i} about maintenance issues",
                "response": f"Sample response {i} with relevant information",
                "timestamp": "2024-01-15T10:00:00Z",
                "processing_time_ms": 150 + i * 10,
                "sources_count": 1,
                "query_type": "general"
            }
            for i in range(1, min(size + 1, 6))  # Mock 5 queries max
        ]
        
        history_result = {
            "queries": mock_queries,
            "pagination": {
                "page": page,
                "size": size,
                "total": len(mock_queries),
                "pages": 1
            },
            "filters": {
                "start_date": start_date,
                "end_date": end_date
            },
            "message": "RAG pipeline not available - mock query history provided."
        }
        
        return history_result
        
    except Exception as e:
        logger.error(f"Query history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Query history retrieval failed")

@query_router.get("/suggestions")
async def get_query_suggestions(
    category: Optional[str] = None,
    limit: Optional[int] = Form(10)
) -> Dict[str, Any]:
    """
    Get suggested queries based on common maintenance topics
    
    Returns helpful query suggestions for users
    """
    try:
        # Validate limit parameter
        if limit and (limit < 1 or limit > 50):
            limit = 10
        
        # TODO: Implement actual suggestion logic in later phases
        # For now, return mock suggestions
        suggestions_by_category = {
            "general": [
                "What are the most common maintenance issues?",
                "Which aircraft models have the most reports?",
                "What are the typical repair times?",
                "How often do specific parts fail?",
                "What are the safety implications of common defects?"
            ],
            "ata_chapters": [
                "What issues are common in Chapter 32 (Landing Gear)?",
                "How often do Chapter 27 (Flight Controls) problems occur?",
                "What are the typical Chapter 21 (Air Conditioning) failures?",
                "Which Chapter 53 (Fuselage) issues are most critical?"
            ],
            "defect_types": [
                "What causes corrosion in landing gear?",
                "How are cracks detected in flight controls?",
                "What leads to hydraulic leaks?",
                "How is wear measured in moving parts?"
            ]
        }
        
        if category and category in suggestions_by_category:
            suggestions = suggestions_by_category[category][:limit]
        else:
            # Return mixed suggestions from all categories
            all_suggestions = []
            for cat_suggestions in suggestions_by_category.values():
                all_suggestions.extend(cat_suggestions)
            suggestions = all_suggestions[:limit]
        
        suggestions_result = {
            "suggestions": suggestions,
            "category": category or "mixed",
            "total_available": len(suggestions),
            "message": "Query suggestions will be enhanced in Phase 5 with ML-based recommendations."
        }
        
        return suggestions_result
        
    except Exception as e:
        logger.error(f"Query suggestions retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Query suggestions retrieval failed")

@query_router.post("/feedback")
async def submit_query_feedback(
    query_id: str = Form(...),
    helpful: bool = Form(...),
    feedback_text: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Submit feedback on query responses
    
    Allows users to rate response quality and provide additional feedback
    """
    try:
        if not query_id:
            raise HTTPException(
                status_code=400,
                detail="Query ID is required"
            )
        
        # Get RAG pipeline
        rag_pipeline = get_rag_pipeline()
        
        if rag_pipeline and hasattr(rag_pipeline, 'vector_store'):
            try:
                # Convert helpful boolean to rating (1-5 scale)
                rating = 5 if helpful else 2
                
                # Update feedback in database
                success = await rag_pipeline.vector_store.update_query_feedback(
                    query_id=query_id,
                    rating=rating,
                    feedback_text=feedback_text or ""
                )
                
                if success:
                    feedback_result = {
                        "feedback_id": f"feedback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                        "query_id": query_id,
                        "helpful": helpful,
                        "feedback_text": feedback_text,
                        "submitted_at": datetime.utcnow().isoformat(),
                        "status": "submitted",
                        "message": "Feedback submitted successfully and stored in database."
                    }
                    
                    logger.info(f"Feedback submitted for query {query_id}: helpful={helpful}")
                    return feedback_result
                else:
                    logger.warning(f"Failed to update feedback for query {query_id}")
                    # Fall through to mock response
                    
            except Exception as e:
                logger.error(f"Error submitting feedback to database: {e}")
                # Fall through to mock response
        
        # Fallback to mock response
        feedback_result = {
            "feedback_id": f"mock_feedback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            "query_id": query_id,
            "helpful": helpful,
            "feedback_text": feedback_text,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "submitted",
            "message": "Feedback received but not stored (RAG pipeline not available)."
        }
        
        logger.info(f"Mock feedback submitted for query {query_id}: helpful={helpful}")
        
        return feedback_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail="Feedback submission failed")

@query_router.get("/stats/usage")
async def get_query_usage_stats() -> Dict[str, Any]:
    """
    Get query usage statistics
    
    Returns metrics about query volume, response times, and user engagement
    """
    try:
        # Get RAG pipeline
        rag_pipeline = get_rag_pipeline()
        
        if rag_pipeline:
            try:
                # Get pipeline statistics
                pipeline_stats = await rag_pipeline.get_pipeline_stats()
                
                usage_stats = {
                    "total_queries": pipeline_stats.get('total_queries_processed', 0),
                    "queries_today": 0,  # Would need date filtering to implement
                    "queries_this_week": 0,  # Would need date filtering to implement
                    "queries_this_month": 0,  # Would need date filtering to implement
                    "average_response_time_ms": 0,  # Would need to calculate from history
                    "most_common_queries": [],  # Would need query analysis
                    "user_satisfaction_score": 0.0,  # Would need feedback analysis
                    "total_reports_available": pipeline_stats.get('total_reports_available', 0),
                    "reports_by_ata_chapter": pipeline_stats.get('reports_by_ata_chapter', {}),
                    "reports_by_severity": pipeline_stats.get('reports_by_severity', {}),
                    "pipeline_status": pipeline_stats.get('pipeline_status', 'unknown'),
                    "last_updated": pipeline_stats.get('last_updated', datetime.utcnow().isoformat()),
                    "message": "Usage statistics retrieved from RAG pipeline."
                }
                
                return usage_stats
                
            except Exception as e:
                logger.error(f"Error retrieving pipeline statistics: {e}")
                # Fall through to mock response
        
        # Fallback to mock response
        usage_stats = {
            "total_queries": 0,
            "queries_today": 0,
            "queries_this_week": 0,
            "queries_this_month": 0,
            "average_response_time_ms": 0,
            "most_common_queries": [],
            "user_satisfaction_score": 0.0,
            "total_reports_available": 0,
            "reports_by_ata_chapter": {},
            "reports_by_severity": {},
            "pipeline_status": "unavailable",
            "last_updated": datetime.utcnow().isoformat(),
            "message": "RAG pipeline not available - mock statistics provided."
        }
        
        return usage_stats
        
    except Exception as e:
        logger.error(f"Usage statistics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Usage statistics retrieval failed")

# Add new RAG-specific endpoints

@query_router.get("/rag/health")
async def get_rag_health() -> Dict[str, Any]:
    """
    Get RAG pipeline health status
    
    Returns health information for all RAG components
    """
    try:
        rag_pipeline = get_rag_pipeline()
        
        if not rag_pipeline:
            return {
                "status": "unavailable",
                "message": "RAG pipeline not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get comprehensive health check
        health_status = await rag_pipeline.health_check()
        
        return health_status
        
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@query_router.post("/query/streaming")
async def process_streaming_query(
    query_text: str = Form(...),
    max_results: Optional[int] = Form(10),
    similarity_threshold: Optional[float] = Form(0.5),
    temperature: Optional[float] = Form(0.7)
):
    """
    Process a streaming query using RAG pipeline
    
    Returns streaming response chunks for real-time user experience
    """
    from fastapi.responses import StreamingResponse
    import json
    
    try:
        if not query_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Query text cannot be empty"
            )
        
        # Get RAG pipeline
        rag_pipeline = get_rag_pipeline()
        
        if not rag_pipeline:
            # Return error for streaming
            async def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': 'RAG pipeline not available'})}\n\n"
            
            return StreamingResponse(error_stream(), media_type="text/plain")
        
        # Create streaming response
        async def stream_response():
            try:
                async for chunk in rag_pipeline.process_streaming_query(
                    query=query_text,
                    max_results=max_results or 10,
                    similarity_threshold=similarity_threshold or 0.5,
                    temperature=temperature or 0.7
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
                # Send end marker
                yield f"data: {json.dumps({'type': 'end'})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming query error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(stream_response(), media_type="text/plain")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming query setup failed: {e}")
        raise HTTPException(status_code=500, detail="Streaming query setup failed")

