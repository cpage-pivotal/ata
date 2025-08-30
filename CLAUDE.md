# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Boeing Aircraft Maintenance Report System - An AI-powered maintenance report management system that ingests maintenance reports, classifies them according to ATA Spec 100 and iSpec 2200 standards, and provides RAG-powered natural language queries.

**Current Status**: Phase 4 complete (Vector Store Implementation). Real-time classification and persistent storage of maintenance reports with pgvector integration, embedding generation, and similarity search. RAG pipeline implementation remains (Phase 5).

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python start.py
# or
python -m app.main

# Test application structure
python test_app.py

# Test classification system (Phase 3)
python test_classification.py

# Test vector store implementation (Phase 4)
python test_vectorstore.py

# Run tests (when implemented)
pytest
```

### Environment Setup
```bash
export ENVIRONMENT=development
export DEBUG=true
export LOG_LEVEL=INFO
```

### Cloud Foundry Deployment
```bash
# Deploy application
cf push boeing-maintenance-system

# Bind services
cf bind-service boeing-maintenance-system postgresql-service
cf bind-service boeing-maintenance-system genai-service

# Restart with new bindings
cf restart boeing-maintenance-system
```

## Architecture

### Core Structure
- **FastAPI Application**: `app/main.py` - Main entry point with CORS, routers, startup/shutdown events
- **Configuration**: `app/config.py` - VCAP_SERVICES parsing and environment management
- **Health Checks**: `app/health.py` - Comprehensive health monitoring endpoints
- **Reports Management**: `app/reports.py` - File upload, ingestion, listing with real-time classification and persistent storage
- **Query Processing**: `app/query.py` - Natural language queries with mock RAG pipeline
- **Classification System**: `app/classification/` - ATA, iSpec 2200, and defect type classification (Phase 3)
- **Vector Store System**: `app/vectorstore/` - pgvector integration, embedding generation, and similarity search (Phase 4)

### Configuration System
The app uses VCAP_SERVICES (Cloud Foundry) for service binding configuration:
- PostgreSQL credentials automatically parsed from `postgresql` service
- GenAI API credentials from `genai-service` binding
- Environment variables override VCAP_SERVICES settings

### Classification System Architecture (Phase 3 - Implemented)
The classification system uses a multi-layered approach:
- **ATA Classifier**: `ata_classifier.py` - Maps reports to ATA Spec 100 chapters using keyword matching and contextual rules
- **iSpec Classifier**: `ispec_classifier.py` - Identifies aircraft parts and extracts part numbers using aerospace patterns
- **Defect Type Classifier**: `type_classifier.py` - Detects defect types, maintenance actions, and severity levels
- **Classifier Service**: `classifier_service.py` - Orchestrates all classifiers with cross-validation and metadata enhancement

### Vector Store Architecture (Phase 4 - Implemented)
The vector store system provides persistent storage and similarity search:
- **Database Models**: `models.py` - SQLAlchemy models with pgvector support for maintenance reports and query history
- **Embedding Service**: `embedding_service.py` - Text-to-vector conversion using GenAI service with batch processing
- **Vector Store Service**: `vectorstore_service.py` - CRUD operations, similarity search, and database management
- **Integration**: Automatic initialization in `main.py` with fallback to localhost PostgreSQL credentials

### Planned Architecture (Future Phases)
- **RAG Pipeline**: `app/rag/` - Retrieval-Augmented Generation implementation  
- **GenAI Client**: `app/genai/` - Enhanced Tanzu GenAI service integration

## Key APIs

### Health Monitoring
- `GET /api/health` - Basic health with service status
- `GET /api/health/ready` - Readiness check for Cloud Foundry
- `GET /api/health/live` - Liveness check
- `GET /api/health/detailed` - Comprehensive system status

### Reports (Enhanced with Classification and Vector Storage)
- `POST /api/reports/upload` - Batch file upload with real-time classification and storage (.txt, .csv)
- `POST /api/reports/ingest` - Single report ingestion with classification and storage
- `POST /api/reports/classify` - Test classification without storing (Phase 3)
- `POST /api/reports/search` - Semantic similarity search using vector embeddings (Phase 4)
- `GET /api/reports/classification/health` - Classification system health check (Phase 3)
- `GET /api/reports/vectorstore/health` - Vector store system health check (Phase 4)
- `GET /api/reports/` - List with pagination and filtering from persistent storage
- `GET /api/reports/{id}` - Individual report details from persistent storage

### Natural Language Queries
- `POST /api/query` - Process natural language queries
- `GET /api/query/history` - Query history with pagination
- `GET /api/query/suggestions` - Pre-built query suggestions
- `POST /api/query/feedback` - Submit response feedback

## Technical Notes

### Dependencies
- FastAPI 0.115+ with uvicorn for async web server
- SQLAlchemy 2.0+ with asyncpg for PostgreSQL
- pgvector for vector similarity search
- OpenAI SDK for GenAI service compatibility
- Pydantic 2.0+ for data validation

### Classification System Implementation (Phase 3)
The classification system is fully operational with real-time processing:
- **ATA Classification**: 75% accuracy on test data, covers ATA chapters 05-80
- **Part Identification**: Extracts aircraft parts, components, and part numbers
- **Defect Detection**: Identifies defects (corrosion, cracks, leaks) and maintenance actions
- **Processing Speed**: ~100ms per report
- **Error Handling**: Comprehensive error handling with health monitoring

### Classification System Usage
The classification system processes maintenance reports through three parallel classifiers:

```python
from app.classification import ClassifierService

service = ClassifierService()
classification = service.classify_report(
    report_text="Found corrosion on wing structure", 
    metadata={"aircraft_type": "Boeing 737-800"}
)
```

**Key Classification Patterns:**
- **Structural Work**: Reports mentioning corrosion, cracks, or SRM references typically classify as ATA 51
- **Landing Gear**: "gear", "strut", "wheel", "brake" keywords typically classify as ATA 32  
- **Flight Controls**: "spoiler", "aileron", "elevator", "actuator" keywords typically classify as ATA 27
- **Electrical**: "connector", "wire", "bonding strap" keywords typically classify as ATA 24

**Cross-Validation Rules**: The system validates classifications across different classifiers (e.g., ATA 32 + gear parts = consistent)

### Vector Store Implementation (Phase 4)
The vector store system is fully operational with persistent PostgreSQL storage and semantic search:
- **Persistent Storage**: All maintenance reports stored in PostgreSQL with pgvector extension
- **Embedding Generation**: Text-to-vector conversion using GenAI service (1536-dimensional embeddings)
- **Similarity Search**: Semantic search using cosine distance with configurable thresholds
- **Batch Processing**: Efficient batch storage and embedding generation for file uploads
- **Database Fallback**: Automatic fallback to localhost:5432 with postgres/postgres credentials

### Vector Store Usage
The vector store integrates seamlessly with classification and provides persistent storage:

```python
from app.vectorstore import VectorStoreService, EmbeddingService

# Initialize services (handled automatically in main.py)
embedding_service = EmbeddingService(api_key, base_url)
vector_store = VectorStoreService(database_url, embedding_service)

# Store classified report
report_id = await vector_store.store_report(
    report_text="Found hydraulic leak at nose gear actuator",
    classification=classification_results,
    aircraft_model="Boeing 737-800"
)

# Semantic search
results = await vector_store.similarity_search(
    query_text="hydraulic problems",
    limit=10,
    similarity_threshold=0.7
)
```

**Key Vector Store Features:**
- **Automatic Database Setup**: Creates tables and enables pgvector extension on startup
- **Embedding Caching**: Efficient embedding generation with batch processing
- **Filtered Search**: Similarity search with ATA chapter, severity, and defect type filters  
- **Query History**: Persistent storage of queries and responses for analytics
- **Health Monitoring**: Comprehensive health checks for database and embedding service

### Testing Strategy
- Use `python test_app.py` to verify module imports and configuration
- Use `python test_classification.py` to test the classification system with sample data
- Use `python test_vectorstore.py` to test the complete Phase 4 vector store implementation
- Health endpoints provide immediate feedback on service and database configuration
- Classification endpoints can be tested with real maintenance report text
- Vector store endpoints support both real GenAI embeddings and mock embeddings for testing
- Sample test data is available in `test_data_reports.py`, `sample_reports.txt`, and `test_vectorstore.py`
- All endpoints include proper validation, error handling, and graceful fallback