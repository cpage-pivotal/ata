# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Boeing Aircraft Maintenance Report System - An AI-powered maintenance report management system that ingests maintenance reports, classifies them according to ATA Spec 100 and iSpec 2200 standards, and provides RAG-powered natural language queries.

**Current Status**: Phase 2 complete (FastAPI core structure). Mock endpoints implemented with TODO markers for future phases.

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
- **Reports Management**: `app/reports.py` - File upload, ingestion, listing with mock responses
- **Query Processing**: `app/query.py` - Natural language queries with mock RAG pipeline

### Configuration System
The app uses VCAP_SERVICES (Cloud Foundry) for service binding configuration:
- PostgreSQL credentials automatically parsed from `postgresql` service
- GenAI API credentials from `genai-service` binding
- Environment variables override VCAP_SERVICES settings

### Planned Architecture (Future Phases)
- **Classification**: `app/classification/` - ATA Spec 100 and iSpec 2200 classification modules
- **Vector Store**: `app/vectorstore/` - pgvector integration for embeddings
- **RAG Pipeline**: `app/rag/` - Retrieval-Augmented Generation implementation
- **GenAI Client**: `app/genai/` - Tanzu GenAI service integration

## Key APIs

### Health Monitoring
- `GET /api/health` - Basic health with service status
- `GET /api/health/ready` - Readiness check for Cloud Foundry
- `GET /api/health/live` - Liveness check
- `GET /api/health/detailed` - Comprehensive system status

### Reports
- `POST /api/reports/upload` - Batch file upload (.txt, .csv)
- `POST /api/reports/ingest` - Single report ingestion
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

### Current Implementation State
All endpoints are implemented with mock responses and clear TODO markers. The application structure is complete and ready for integration with actual services in future phases.

### Testing Strategy
- Use `python test_app.py` to verify module imports and configuration
- Health endpoints provide immediate feedback on service configuration
- All endpoints include proper validation and error handling