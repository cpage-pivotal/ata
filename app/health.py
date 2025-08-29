"""
Health check router for Boeing Aircraft Maintenance Report System
Provides endpoints for monitoring system health and status
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Dict, Any

from app.config import get_settings

logger = logging.getLogger(__name__)
health_router = APIRouter()

@health_router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    Returns system status and basic information
    """
    try:
        settings = get_settings()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Boeing Aircraft Maintenance Report System",
            "version": "1.0.0",
            "environment": settings.environment,
            "checks": {
                "config": "ok",
                "database": "unknown",  # Will be updated when DB connection is implemented
                "genai": "unknown"      # Will be updated when GenAI client is implemented
            }
        }
        
        # Check configuration
        if settings.database.database_url:
            health_status["checks"]["database"] = "configured"
        else:
            health_status["checks"]["database"] = "not_configured"
        
        if settings.genai.genai_api_key:
            health_status["checks"]["genai"] = "configured"
        else:
            health_status["checks"]["genai"] = "not_configured"
        
        # Overall status based on critical checks
        critical_checks = ["database", "genai"]
        if all(health_status["checks"][check] == "configured" for check in critical_checks):
            health_status["status"] = "healthy"
        elif any(health_status["checks"][check] == "not_configured" for check in critical_checks):
            health_status["status"] = "degraded"
        else:
            health_status["status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@health_router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint
    Returns whether the service is ready to handle requests
    """
    try:
        settings = get_settings()
        
        # Check if critical services are configured
        database_ready = bool(settings.database.database_url)
        genai_ready = bool(settings.genai.genai_api_key)
        
        ready = database_ready and genai_ready
        
        readiness_status = {
            "ready": ready,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "ready" if database_ready else "not_ready",
                "genai": "ready" if genai_ready else "not_ready"
            }
        }
        
        if not ready:
            raise HTTPException(status_code=503, detail="Service not ready")
        
        return readiness_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=500, detail="Readiness check failed")

@health_router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint
    Returns whether the service is alive and running
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Boeing Aircraft Maintenance Report System"
    }

@health_router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check endpoint
    Returns comprehensive system status information
    """
    try:
        settings = get_settings()
        
        detailed_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Boeing Aircraft Maintenance Report System",
            "version": "1.0.0",
            "environment": settings.environment,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "configuration": {
                "database": {
                    "configured": bool(settings.database.database_url),
                    "host": settings.database.database_host,
                    "port": settings.database.database_port,
                    "database": settings.database.database_name,
                    "user": settings.database.database_user
                },
                "genai": {
                    "configured": bool(settings.genai.genai_api_key),
                    "base_url": settings.genai.genai_base_url,
                    "model": settings.genai.genai_model,
                    "embedding_model": settings.genai.genai_embedding_model
                }
            },
            "system_info": {
                "python_version": "3.11+",  # Will be updated with actual version
                "fastapi_version": "0.115+",
                "platform": "Cloud Foundry"
            }
        }
        
        return detailed_status
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Detailed health check failed")

