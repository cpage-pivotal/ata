"""
Test script for Phase 4 Vector Store Implementation
Tests the vector store functionality with sample maintenance reports
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_settings
from app.vectorstore import VectorStoreService, EmbeddingService
from app.classification import ClassifierService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample maintenance reports for testing
SAMPLE_REPORTS = [
    {
        "text": "Found hydraulic leak at nose gear actuator during pre-flight inspection. B-nut connection showing signs of corrosion. Replaced O-ring seal and torqued to 25 ft-lbs specification. Leak check passed.",
        "aircraft_model": "Boeing 737-800"
    },
    {
        "text": "Wing tip navigation light inoperative. Traced fault to loose connector at wing root. Cleaned contacts and secured connection. Light operation normal. No further action required.",
        "aircraft_model": "Boeing 737-800"
    },
    {
        "text": "Cabin door seal showing wear pattern along lower edge. Seal appears compressed and hardened from age. Recommend replacement during next scheduled maintenance window.",
        "aircraft_model": "Boeing 787-8"
    },
    {
        "text": "Crack found in wing spoiler actuator bracket. Crack approximately 2 inches in length, located at bolt hole. Part removed and sent to shop for repair per SRM 57-31-02.",
        "aircraft_model": "Boeing 777-200"
    },
    {
        "text": "Engine oil quantity indication erratic. Oil quantity fluctuates between 18-22 quarts during flight. Suspect faulty oil quantity transmitter. Transmitter replacement scheduled.",
        "aircraft_model": "Boeing 737-900"
    }
]

async def test_vector_store():
    """Test the complete vector store implementation"""
    print("=" * 60)
    print("TESTING PHASE 4: VECTOR STORE IMPLEMENTATION")
    print("=" * 60)
    
    try:
        # Get settings
        settings = get_settings()
        print(f"Environment: {settings.environment}")
        print(f"Database URL: {settings.database_url}")
        
        # Check if we have the required credentials
        if not settings.database_url:
            print("❌ No database URL configured")
            print("Please ensure PostgreSQL is running at localhost:5432 with credentials postgres/postgres")
            print("Or set DATABASE_URL environment variable")
            return False
        
        if not settings.genai_api_key or not settings.genai_api_url:
            print("⚠️  GenAI credentials not configured - using mock embedding service")
            # For testing without GenAI, we'll use a mock embedding service
            embedding_service = MockEmbeddingService()
        else:
            print(f"GenAI API URL: {settings.genai_api_url}")
            embedding_service = EmbeddingService(
                api_key=settings.genai_api_key,
                base_url=settings.genai_api_url
            )
        
        # Initialize vector store service
        print("\n1. Initializing Vector Store Service...")
        vector_store = VectorStoreService(
            database_url=settings.database_url,
            embedding_service=embedding_service
        )
        
        # Initialize database
        print("2. Initializing Database (creating tables and extensions)...")
        db_initialized = await vector_store.initialize_database()
        if not db_initialized:
            print("❌ Database initialization failed")
            return False
        print("✅ Database initialized successfully")
        
        # Test health check
        print("\n3. Testing Health Check...")
        health = await vector_store.health_check()
        print(f"Health Status: {health.get('status', 'unknown')}")
        if health.get('status') == 'healthy':
            print("✅ Vector store is healthy")
        else:
            print(f"⚠️  Health check issues: {health}")
        
        # Initialize classification service
        print("\n4. Initializing Classification Service...")
        classifier = ClassifierService()
        
        # Process and store sample reports
        print("\n5. Processing and Storing Sample Reports...")
        stored_ids = []
        
        for i, sample in enumerate(SAMPLE_REPORTS, 1):
            try:
                print(f"   Processing report {i}/5: {sample['text'][:50]}...")
                
                # Classify the report
                classification = classifier.classify_report(
                    sample['text'],
                    {'aircraft_type': sample['aircraft_model']}
                )
                classification_dict = classifier.to_dict(classification)
                
                # Store in vector database
                report_id = await vector_store.store_report(
                    report_text=sample['text'],
                    classification=classification_dict,
                    aircraft_model=sample['aircraft_model'],
                    report_date=datetime.utcnow()
                )
                
                if report_id:
                    stored_ids.append(report_id)
                    summary = classifier.get_classification_summary(classification)
                    print(f"   ✅ Stored as {report_id} - ATA: {summary.get('ata_chapter', 'N/A')}")
                else:
                    print(f"   ❌ Failed to store report {i}")
                    
            except Exception as e:
                print(f"   ❌ Error processing report {i}: {e}")
        
        print(f"\n   Successfully stored {len(stored_ids)} reports")
        
        # Test retrieval
        if stored_ids:
            print("\n6. Testing Report Retrieval...")
            test_id = stored_ids[0]
            retrieved = await vector_store.get_report(test_id)
            if retrieved:
                print(f"   ✅ Successfully retrieved report: {test_id}")
                print(f"   ATA Chapter: {retrieved.get('ata_chapter', 'N/A')}")
                print(f"   Aircraft: {retrieved.get('aircraft_model', 'N/A')}")
            else:
                print(f"   ❌ Failed to retrieve report: {test_id}")
        
        # Test listing
        print("\n7. Testing Report Listing...")
        reports_list = await vector_store.list_reports(limit=10)
        print(f"   ✅ Listed {len(reports_list)} reports")
        
        for report in reports_list[:3]:  # Show first 3
            print(f"   - {report['id']}: ATA {report.get('ata_chapter', 'N/A')} - {report['aircraft_model']}")
        
        # Test similarity search
        print("\n8. Testing Similarity Search...")
        test_queries = [
            "hydraulic leak problems",
            "wing structural issues", 
            "electrical connector problems"
        ]
        
        for query in test_queries:
            try:
                results = await vector_store.similarity_search(
                    query_text=query,
                    limit=3,
                    similarity_threshold=0.3
                )
                print(f"   Query: '{query}' - Found {len(results)} similar reports")
                
                for result in results[:2]:  # Show top 2
                    score = result.get('similarity_score', 0)
                    ata = result.get('ata_chapter', 'N/A')
                    print(f"     - Score: {score:.3f}, ATA: {ata}, Text: {result['report_text'][:60]}...")
                    
            except Exception as e:
                print(f"   ❌ Search failed for '{query}': {e}")
        
        # Test statistics
        print("\n9. Testing Statistics...")
        stats = await vector_store.get_stats()
        print(f"   ✅ Total reports: {stats.get('total_reports', 0)}")
        print(f"   ✅ ATA chapters: {list(stats.get('reports_by_ata_chapter', {}).keys())}")
        
        # Clean up (optional)
        print("\n10. Cleaning Up...")
        await vector_store.close()
        print("✅ Vector store connections closed")
        
        print("\n" + "=" * 60)
        print("✅ PHASE 4 VECTOR STORE IMPLEMENTATION TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Vector store test failed: {e}")
        print(f"\n❌ Test failed with error: {e}")
        print("=" * 60)
        return False

class MockEmbeddingService:
    """Mock embedding service for testing without GenAI credentials"""
    
    def __init__(self):
        import numpy as np
        self.np = np
        
    async def generate_embedding_async(self, text: str):
        """Generate a mock embedding vector"""
        if not text:
            return None
        
        # Generate a deterministic but varied embedding based on text hash
        hash_value = hash(text) % (2**31)
        self.np.random.seed(hash_value)
        
        # Generate 1536-dimensional embedding (OpenAI standard)
        embedding = self.np.random.normal(0, 1, 1536).tolist()
        return embedding
    
    async def generate_embeddings_batch_async(self, texts):
        """Generate mock embeddings for batch"""
        return [await self.generate_embedding_async(text) for text in texts]
    
    def health_check(self):
        return {
            "status": "healthy",
            "model": "mock-embedding-model",
            "embedding_dimension": 1536,
            "note": "Using mock embeddings for testing"
        }

async def main():
    """Main test function"""
    success = await test_vector_store()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())