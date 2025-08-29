# Boeing Aircraft Maintenance Report System

## Overview

This is an AI-powered maintenance report management system for Boeing aircraft. The system ingests maintenance reports, classifies them according to ATA Spec 100 and iSpec 2200 standards, stores them in a vector database, and provides a RAG-powered interface for natural language queries.

## Project Structure

```
ata/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration and VCAP_SERVICES parsing
│   ├── health.py                # Health check endpoints
│   ├── reports.py               # Maintenance report management
│   └── query.py                 # Natural language query processing
├── requirements.txt              # Python dependencies
├── maintenance-system-design.md  # System design document
└── README.md                    # This file
```

## Phase 2 Implementation Status

✅ **FastAPI Application Structure** - COMPLETED
- Main application entry point with proper routing
- Configuration module with VCAP_SERVICES integration
- Health check endpoints (basic, readiness, liveness, detailed)
- Reports router with upload, ingestion, and listing endpoints
- Query router with natural language processing endpoints
- CORS middleware for React frontend integration
- Comprehensive logging and error handling

🔄 **Next Steps (Phase 3-4)**
- Database models and migrations
- GenAI client integration
- Classification system implementation
- Vector store implementation

## Quick Start

### Prerequisites

- Python 3.11+
- Cloud Foundry CLI (for deployment)
- PostgreSQL with pgvector extension
- GenAI on Tanzu Platform service

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export ENVIRONMENT=development
   export DEBUG=true
   export LOG_LEVEL=INFO
   ```

3. **Run the application:**
   ```bash
   python -m app.main
   ```

4. **Access the API:**
   - API Documentation: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/api/health
   - Root Endpoint: http://localhost:8000/

### Cloud Foundry Deployment

1. **Push the application:**
   ```bash
   cf push boeing-maintenance-system
   ```

2. **Bind services:**
   ```bash
   cf bind-service boeing-maintenance-system postgresql-service
   cf bind-service boeing-maintenance-system genai-service
   ```

3. **Restart the application:**
   ```bash
   cf restart boeing-maintenance-system
   ```

## API Endpoints

### Health Checks
- `GET /api/health` - Basic health status
- `GET /api/health/ready` - Readiness check
- `GET /api/health/live` - Liveness check
- `GET /api/health/detailed` - Detailed system status

### Reports Management
- `POST /api/reports/upload` - Upload maintenance report files
- `POST /api/reports/ingest` - Ingest single maintenance report
- `GET /api/reports/` - List reports with pagination and filtering
- `GET /api/reports/{report_id}` - Get specific report details
- `GET /api/reports/stats/summary` - Get report statistics

### Natural Language Queries
- `POST /api/query` - Process natural language queries
- `GET /api/query/history` - Get query history
- `GET /api/query/suggestions` - Get query suggestions
- `POST /api/query/feedback` - Submit query feedback
- `GET /api/query/stats/usage` - Get usage statistics

## Configuration

The application automatically configures itself using:

1. **VCAP_SERVICES** (Cloud Foundry)
   - PostgreSQL database credentials
   - GenAI service API keys and endpoints

2. **Environment Variables**
   - `ENVIRONMENT` - Deployment environment
   - `DEBUG` - Debug mode flag
   - `LOG_LEVEL` - Logging level
   - `DATABASE_URL` - Database connection string (overrides VCAP)
   - `GENAI_API_KEY` - GenAI API key (overrides VCAP)
   - `GENAI_BASE_URL` - GenAI base URL (overrides VCAP)

## Development Notes

### Current Implementation
- All endpoints return mock responses with clear TODO markers
- Configuration parsing is fully implemented
- Health checks provide comprehensive system status
- Error handling and logging are implemented throughout

### Phase 3-4 Dependencies
- Database models and connection pooling
- GenAI client with model discovery
- Classification service for ATA/iSpec mapping
- Vector store service for embeddings

### Testing
- Health endpoints can be tested immediately
- Upload endpoints accept files but don't process them yet
- Query endpoints return mock responses
- All endpoints include proper validation and error handling

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive logging for all operations
3. Include proper error handling and HTTP status codes
4. Update this README when adding new features
5. Test endpoints before committing changes

## License

This project is proprietary to Boeing and contains confidential information.

