#!/usr/bin/env python3
"""
Startup script for Boeing Aircraft Maintenance Report System
Provides easy way to start the FastAPI application
"""

import sys
import os
import uvicorn
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        print("✅ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nPlease install dependencies first:")
        print("pip install -r requirements.txt")
        return False

def main():
    """Main startup function"""
    print("=" * 60)
    print("Boeing Aircraft Maintenance Report System")
    print("Starting FastAPI application...")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Set default environment
    os.environ.setdefault('ENVIRONMENT', 'development')
    os.environ.setdefault('DEBUG', 'true')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    print(f"Environment: {os.environ.get('ENVIRONMENT')}")
    print(f"Debug mode: {os.environ.get('DEBUG')}")
    print(f"Log level: {os.environ.get('LOG_LEVEL')}")
    
    try:
        print("\n🚀 Starting FastAPI application...")
        print("API Documentation: http://localhost:8000/api/docs")
        print("Health Check: http://localhost:8000/api/health")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        # Start the application
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

