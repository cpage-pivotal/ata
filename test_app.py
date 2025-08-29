#!/usr/bin/env python3
"""
Simple test script to verify FastAPI application structure
Run this to check that all modules can be imported correctly
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing FastAPI application imports...")
    
    try:
        # Test app package import
        from app import main, config, health, reports, query
        print("✅ All app modules imported successfully")
        
        # Test configuration
        from app.config import get_settings
        settings = get_settings()
        print(f"✅ Configuration loaded: {settings.environment}")
        
        # Test FastAPI app creation
        from app.main import app
        print(f"✅ FastAPI app created: {app.title}")
        
        # Test router imports
        from app.health import health_router
        from app.reports import reports_router
        from app.query import query_router
        print("✅ All routers imported successfully")
        
        print("\n🎉 All imports successful! FastAPI application structure is ready.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_configuration():
    """Test configuration parsing"""
    print("\nTesting configuration...")
    
    try:
        from app.config import get_settings, parse_vcap_services
        
        # Test settings
        settings = get_settings()
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ Debug mode: {settings.debug}")
        print(f"✅ Log level: {settings.log_level}")
        
        # Test VCAP parsing (will be empty in local dev)
        vcap = parse_vcap_services()
        print(f"✅ VCAP_SERVICES parsing: {'configured' if vcap else 'not configured'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Boeing Aircraft Maintenance Report System")
    print("FastAPI Application Structure Test")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test configuration
        config_ok = test_configuration()
        
        if config_ok:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("FastAPI application structure is ready for development.")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Install dependencies: pip install -r requirements.txt")
            print("2. Run the app: python -m app.main")
            print("3. Access API docs: http://localhost:8000/api/docs")
            return 0
        else:
            print("\n❌ Configuration tests failed")
            return 1
    else:
        print("\n❌ Import tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

