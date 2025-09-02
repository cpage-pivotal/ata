"""
Boeing Aircraft Maintenance Report System
Configuration management with VCAP_SERVICES support
"""

import os
import json
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Look for .env file in project root
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from: {env_path}")
    else:
        # Try to load from current directory as fallback
        if Path('.env').exists():
            load_dotenv('.env')
            print("✅ Loaded environment from: ./.env")
except ImportError:
    print("⚠️  python-dotenv not available - using system environment variables only")


class Settings:
    """Application settings with VCAP_SERVICES support"""

    def __init__(self):
        # Environment
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # Database - default to localhost fallback
        self.database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/boeing_maintenance')

        # GenAI Service - Check both GENAI_ and OPENAI_ prefixes for flexibility
        self.genai_api_key = (
                os.getenv('GENAI_API_KEY') or
                os.getenv('OPENAI_API_KEY')
        )
        self.genai_api_url = (
                os.getenv('GENAI_API_URL') or
                os.getenv('OPENAI_API_URL') or
                'https://api.openai.com/v1'  # Default OpenAI URL
        )

        # Model configuration
        self.chat_model = os.getenv('CHAT_MODEL', 'gpt-4o')
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')

        # Debug output for troubleshooting
        self._debug_config()

        # Load from VCAP_SERVICES if available (will override defaults)
        self._load_vcap_services()

    def _debug_config(self):
        """Debug configuration loading (only in development)"""
        if self.environment == 'development':
            print(f"🔧 Configuration Debug:")
            print(f"   Environment: {self.environment}")
            print(f"   Database URL set: {'Yes' if self.database_url else 'No'}")
            print(f"   GenAI API Key set: {'Yes' if self.genai_api_key else 'No'}")
            print(f"   GenAI API URL: {self.genai_api_url}")
            print(f"   Chat Model: {self.chat_model}")
            print(f"   Embedding Model: {self.embedding_model}")

            # Show first/last few chars of API key for debugging (if present)
            if self.genai_api_key and len(self.genai_api_key) > 10:
                masked_key = f"{self.genai_api_key[:8]}...{self.genai_api_key[-4:]}"
                print(f"   API Key Preview: {masked_key}")

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
                print("✅ Loaded database config from VCAP_SERVICES")

            # GenAI service
            if 'genai-service' in services:
                genai_service = services['genai-service'][0]
                credentials = genai_service['credentials']
                self.genai_api_key = credentials.get('api_key')
                self.genai_api_url = credentials.get('api_url')
                print("✅ Loaded GenAI config from VCAP_SERVICES")

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"⚠️  Error parsing VCAP_SERVICES: {e}")


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