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
        if settings.database_url:
            health_status["checks"]["database"] = "configured"
        else:
            health_status["checks"]["database"] = "not_configured"

        if settings.genai_api_key:
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
        database_ready = bool(settings.database_url)
        genai_ready = bool(settings.genai_api_key)

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

        # Parse database URL for detailed info
        db_info = {"configured": bool(settings.database_url)}
        if settings.database_url:
            # Extract info from database URL
            try:
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(settings.database_url)
                db_info.update({
                    "host": parsed.hostname,
                    "port": parsed.port,
                    "database": parsed.path.lstrip('/') if parsed.path else None,
                    "user": parsed.username
                })
            except Exception as e:
                logger.warning(f"Could not parse database URL: {e}")
                db_info["parse_error"] = str(e)

        detailed_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Boeing Aircraft Maintenance Report System",
            "version": "1.0.0",
            "environment": settings.environment,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "configuration": {
                "database": db_info,
                "genai": {
                    "configured": bool(settings.genai_api_key),
                    "base_url": settings.genai_api_url if settings.genai_api_url else None,
                    "chat_model": settings.chat_model,
                    "embedding_model": settings.embedding_model
                }
            },
            "system_info": {
                "python_version": "3.11+",
                "fastapi_version": "0.115+",
                "platform": "Local Development" if settings.environment == "development" else "Cloud Foundry"
            }
        }

        # Set overall status based on configuration
        if settings.database_url and settings.genai_api_key:
            detailed_status["status"] = "healthy"
        elif not settings.database_url and not settings.genai_api_key:
            detailed_status["status"] = "unhealthy"
        else:
            detailed_status["status"] = "degraded"

        return detailed_status

    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Detailed health check failed")