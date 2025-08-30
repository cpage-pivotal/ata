"""
Boeing Aircraft Maintenance Report System
Main FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Optional
import logging

from app.config import get_settings
from app.health import health_router
from app.reports import reports_router, set_vector_store_service
from app.query import query_router

# Vector store imports - Phase 4 implementation
from app.vectorstore import VectorStoreService, EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Boeing Aircraft Maintenance Report System",
    description="AI-powered maintenance report management system with ATA/iSpec classification",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(query_router, prefix="/api", tags=["query"])

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting Boeing Aircraft Maintenance Report System")
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL configured: {bool(settings.database_url)}")
    logger.info(f"GenAI API configured: {bool(settings.genai_api_key)}")
    
    # Initialize vector store service if credentials available (Phase 4)
    if settings.database_url and settings.genai_api_key and settings.genai_api_url:
        try:
            # Initialize embedding service
            embedding_service = EmbeddingService(
                api_key=settings.genai_api_key,
                base_url=settings.genai_api_url
            )
            
            # Initialize vector store service
            vector_store = VectorStoreService(
                database_url=settings.database_url,
                embedding_service=embedding_service
            )
            
            # Initialize database (create tables and extensions)
            db_initialized = await vector_store.initialize_database()
            if db_initialized:
                # Set the vector store service in reports module
                set_vector_store_service(vector_store)
                logger.info("Vector store service initialized successfully (Phase 4)")
            else:
                logger.warning("Vector store database initialization failed")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector store service: {e}")
            logger.info("Application will run without vector store (Phase 3 mode)")
    else:
        logger.info("Vector store not initialized - missing database or GenAI credentials")
        logger.info("Application running in Phase 3 mode (classification only)")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down Boeing Aircraft Maintenance Report System")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Boeing Aircraft Maintenance Report System",
        "version": "1.0.0",
        "status": "operational"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

