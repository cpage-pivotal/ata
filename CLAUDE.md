# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Boeing Aircraft Maintenance Report System - An AI-powered maintenance report management system that ingests maintenance reports, classifies them according to ATA Spec 100 and iSpec 2200 standards, and provides RAG-powered natural language queries.

**Current Status**: Phase 3 complete (Classification System). Real-time classification of maintenance reports with ATA chapter mapping, part identification, and defect type detection. Mock endpoints remain for vector store and RAG pipeline (Phase 4-5).

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
- **Reports Management**: `app/reports.py` - File upload, ingestion, listing with real-time classification
- **Query Processing**: `app/query.py` - Natural language queries with mock RAG pipeline
- **Classification System**: `app/classification/` - ATA, iSpec 2200, and defect type classification (Phase 3)

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

### Planned Architecture (Future Phases)
- **Vector Store**: `app/vectorstore/` - pgvector integration for embeddings
- **RAG Pipeline**: `app/rag/` - Retrieval-Augmented Generation implementation
- **GenAI Client**: `app/genai/` - Tanzu GenAI service integration

## Key APIs

### Health Monitoring
- `GET /api/health` - Basic health with service status
- `GET /api/health/ready` - Readiness check for Cloud Foundry
- `GET /api/health/live` - Liveness check
- `GET /api/health/detailed` - Comprehensive system status

### Reports (Enhanced with Classification)
- `POST /api/reports/upload` - Batch file upload with real-time classification (.txt, .csv)
- `POST /api/reports/ingest` - Single report ingestion with classification
- `POST /api/reports/classify` - Test classification without storing (Phase 3)
- `GET /api/reports/classification/health` - Classification system health check (Phase 3)
- `GET /api/reports/` - List with pagination and filtering
- `GET /api/reports/{id}` - Individual report details

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

### Testing Strategy
- Use `python test_app.py` to verify module imports and configuration
- Use `python test_classification.py` to test the classification system with sample data
- Health endpoints provide immediate feedback on service configuration
- Classification endpoints can be tested with real maintenance report text
- Sample test data is available in `test_data_reports.py` and `sample_reports.txt`
- All endpoints include proper validation and error handling