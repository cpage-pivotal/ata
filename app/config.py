"""
Boeing Aircraft Maintenance Report System
Configuration management with VCAP_SERVICES support
"""

import os
import json
from typing import Optional


class Settings:
    """Application settings with VCAP_SERVICES support"""
    
    def __init__(self):
        # Environment
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Database - default to localhost fallback
        self.database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/boeing_maintenance')
        
        # GenAI Service
        self.genai_api_key = os.getenv('GENAI_API_KEY')
        self.genai_api_url = os.getenv('GENAI_API_URL')
        
        # Load from VCAP_SERVICES if available (will override defaults)
        self._load_vcap_services()
    
    def _load_vcap_services(self):
        """Load configuration from VCAP_SERVICES (Cloud Foundry)"""
        vcap_services = os.getenv('VCAP_SERVICES')
        if not vcap_services:
            return
        
        try:
            services = json.loads(vcap_services)
            
            # PostgreSQL service
            if 'postgresql' in services:
                postgres_service = services['postgresql'][0]
                credentials = postgres_service['credentials']
                self.database_url = (
                    f"postgresql+asyncpg://{credentials['username']}:"
                    f"{credentials['password']}@{credentials['hostname']}:"
                    f"{credentials['port']}/{credentials['database']}"
                )
            
            # GenAI service
            if 'genai-service' in services:
                genai_service = services['genai-service'][0]
                credentials = genai_service['credentials']
                self.genai_api_key = credentials.get('api_key')
                self.genai_api_url = credentials.get('api_url')
                
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # Log error but continue with environment variables
            pass


_settings = None

def get_settings() -> Settings:
    """Get cached settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def parse_vcap_services() -> Optional[dict]:
    """Parse VCAP_SERVICES environment variable"""
    vcap_services = os.getenv('VCAP_SERVICES')
    if not vcap_services:
        return None
    
    try:
        return json.loads(vcap_services)
    except json.JSONDecodeError:
        return None