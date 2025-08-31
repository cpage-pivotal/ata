#!/usr/bin/env python3
"""
Test suite for RAG Pipeline implementation - Phase 5
Boeing Aircraft Maintenance Report System

This test suite validates the complete RAG pipeline functionality including:
- Retrieval component testing
- Generation component testing  
- Complete pipeline orchestration
- Integration with vector store and GenAI services
- Query processing and response generation
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test data
SAMPLE_MAINTENANCE_REPORTS = [
    {
        "id": "test_report_1",
        "report_text": "Found hydraulic leak at nose gear actuator. B-nut connection showing signs of corrosion. Replaced seal and torqued to specification per AMM 32-42-01.",
        "aircraft_model": "Boeing 737-800",
        "ata_chapter": "32",
        "ata_chapter_name": "Landing Gear",
        "defect_types": ["leak", "corrosion"],
        "maintenance_actions": ["replace", "torque"],
        "severity": "minor",
        "safety_critical": "false",
        "similarity_score": 0.95,
        "created_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": "test_report_2", 
        "report_text": "Crack found in flight control actuator bracket. Crack length 2.5 inches, exceeds limits. Replaced bracket assembly per SRM 27-31-02.",
        "aircraft_model": "Boeing 737-800",
        "ata_chapter": "27",
        "ata_chapter_name": "Flight Controls",
        "defect_types": ["crack"],
        "maintenance_actions": ["replace"],
        "severity": "major",
        "safety_critical": "true",
        "similarity_score": 0.88,
        "created_at": "2024-01-14T14:30:00Z"
    },
    {
        "id": "test_report_3",
        "report_text": "Air conditioning pack temperature sensor reading erratic. Sensor replaced and system tested satisfactory.",
        "aircraft_model": "Boeing 737-900",
        "ata_chapter": "21",
        "ata_chapter_name": "Air Conditioning",
        "defect_types": ["malfunction"],
        "maintenance_actions": ["replace", "test"],
        "severity": "moderate",
        "safety_critical": "false",
        "similarity_score": 0.72,
        "created_at": "2024-01-13T09:15:00Z"
    }
]

SAMPLE_QUERIES = [
    {
        "query": "What hydraulic issues have been reported?",
        "expected_type": "general",
        "expected_ata": "32"
    },
    {
        "query": "Are there any safety-critical cracks in flight controls?",
        "expected_type": "safety_critical",
        "expected_ata": "27"
    },
    {
        "query": "What are the trends in air conditioning failures?",
        "expected_type": "trend_analysis",
        "expected_ata": "21"
    },
    {
        "query": "Tell me about Chapter 32 landing gear problems",
        "expected_type": "ata_specific",
        "expected_ata": "32"
    }
]


class MockEmbeddingService:
    """Mock embedding service for testing without GenAI credentials"""
    
    def __init__(self):
        self.model = "mock-embedding-model"
    
    async def generate_embedding_async(self, text: str) -> List[float]:
        """Generate mock embedding based on text content"""
        # Create deterministic embeddings based on text hash
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to 1536-dimensional vector (matching OpenAI ada-002)
        embedding = []
        for i in range(1536):
            # Use hash characters cyclically to generate float values
            char_idx = i % len(text_hash)
            char_val = ord(text_hash[char_idx])
            # Normalize to [-1, 1] range
            embedding.append((char_val - 128) / 128.0)
        
        return embedding
    
    async def generate_embeddings_batch_async(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings"""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding_async(text)
            embeddings.append(embedding)
        return embeddings
    
    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "model": self.model,
            "embedding_dimension": 1536
        }


class MockChatService:
    """Mock chat service for testing without GenAI credentials"""
    
    def __init__(self):
        self.model = "mock-chat-model"
    
    async def generate_response_async(self, messages: List[Dict[str, str]], 
                                    temperature: float = 0.7, 
                                    max_tokens: int = None) -> str:
        """Generate mock response based on query content"""
        # Extract user query from messages
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Generate contextual mock response
        if "hydraulic" in user_message.lower():
            return "Based on the maintenance reports, hydraulic issues have been identified in the landing gear system (ATA Chapter 32). The most common problem is hydraulic leaks at actuator connections, often caused by seal deterioration and corrosion. These issues are typically classified as minor severity but require prompt attention to prevent system failures."
        
        elif "safety" in user_message.lower() and "crack" in user_message.lower():
            return "⚠️ SAFETY-CRITICAL ANALYSIS ⚠️\n\nBased on the maintenance reports, there are safety-critical crack issues in flight control systems (ATA Chapter 27). A crack was found in a flight control actuator bracket exceeding allowable limits. This is classified as major severity and safety-critical. Immediate replacement was performed per structural repair manual procedures. Regular inspection of flight control components is essential for flight safety."
        
        elif "trend" in user_message.lower():
            return "Trend analysis of the maintenance reports shows the following patterns:\n\n1. Landing gear issues (32%) - primarily hydraulic leaks and corrosion\n2. Flight control problems (25%) - structural cracks and actuator failures\n3. Air conditioning failures (20%) - sensor malfunctions and temperature control issues\n\nThe data suggests a need for enhanced preventive maintenance programs, particularly for hydraulic systems and structural components."
        
        elif "chapter 32" in user_message.lower() or "landing gear" in user_message.lower():
            return "ATA Chapter 32 (Landing Gear) analysis shows common issues include:\n\n- Hydraulic leaks at actuator connections\n- Corrosion of metal components, particularly B-nut connections\n- Seal deterioration leading to fluid loss\n\nMaintenance actions typically involve seal replacement, corrosion treatment, and proper torquing per AMM specifications. Most issues are minor severity but require timely attention to prevent operational disruptions."
        
        else:
            return f"Based on the available maintenance reports, I can provide information about aircraft maintenance issues. The query '{user_message[:100]}...' has been processed and relevant maintenance data has been analyzed. Please refer to the source citations for specific report details."
    
    async def generate_response_stream(self, messages: List[Dict[str, str]], 
                                     temperature: float = 0.7, 
                                     max_tokens: int = None):
        """Generate streaming mock response"""
        response = await self.generate_response_async(messages, temperature, max_tokens)
        
        # Split response into chunks for streaming
        words = response.split()
        chunk_size = 5
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size]) + " "
            yield chunk
            await asyncio.sleep(0.1)  # Simulate streaming delay
    
    def create_messages(self, system_prompt: str, user_query: str, context: str = None) -> List[Dict[str, str]]:
        """Create message list for chat completion"""
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.append({
                "role": "user", 
                "content": f"Context:\n{context}\n\nQuestion: {user_query}"
            })
        else:
            messages.append({"role": "user", "content": user_query})
        
        return messages
    
    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "model": self.model,
            "test_response": "OK"
        }


class MockVectorStore:
    """Mock vector store for testing"""
    
    def __init__(self):
        self.reports = SAMPLE_MAINTENANCE_REPORTS.copy()
        self.queries = []
    
    async def similarity_search(self, query_text: str, limit: int = 10, 
                               similarity_threshold: float = 0.5, 
                               filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Mock similarity search"""
        # Simple keyword-based matching for testing
        results = []
        
        for report in self.reports:
            score = 0.0
            query_lower = query_text.lower()
            report_text_lower = report["report_text"].lower()
            
            # Calculate mock similarity based on keyword overlap and semantic matching
            query_words = set(query_lower.split())
            report_words = set(report_text_lower.split())
            
            # Direct keyword overlap
            if query_words & report_words:
                overlap = len(query_words & report_words)
                score = min(overlap / max(len(query_words), 1), 1.0)
            
            # Semantic matching for better test coverage
            semantic_matches = {
                "hydraulic": ["hydraulic", "leak", "fluid", "actuator", "seal"],
                "crack": ["crack", "fracture", "break", "structural", "bracket"],
                "air conditioning": ["air", "conditioning", "temperature", "sensor", "pack"],
                "landing gear": ["landing", "gear", "nose", "actuator", "hydraulic"],
                "flight control": ["flight", "control", "actuator", "bracket"],
                "safety": ["safety", "critical", "major", "dangerous"],
                "trend": ["pattern", "recurring", "frequent", "multiple", "analysis"]
            }
            
            for key, keywords in semantic_matches.items():
                if key in query_lower:
                    for keyword in keywords:
                        if keyword in report_text_lower:
                            score = max(score, 0.7)  # Boost semantic matches
                            break
            
            # Apply filters
            if filters:
                if filters.get("ata_chapter") and report["ata_chapter"] != filters["ata_chapter"]:
                    continue
                if filters.get("severity") and report["severity"] != filters["severity"]:
                    continue
                if filters.get("defect_type") and filters["defect_type"] not in report.get("defect_types", []):
                    continue
            
            if score >= similarity_threshold:
                report_copy = report.copy()
                report_copy["similarity_score"] = score
                results.append(report_copy)
        
        # Sort by similarity score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return results[:limit]
    
    async def store_query(self, query_text: str, response_text: str, 
                         sources: List[Dict[str, Any]], processing_time_ms: int,
                         query_type: str = "natural_language") -> str:
        """Mock query storage"""
        query_id = f"mock_query_{len(self.queries) + 1}"
        
        query_record = {
            "id": query_id,
            "query_text": query_text,
            "response_text": response_text,
            "sources": sources,
            "processing_time_ms": str(processing_time_ms),
            "query_type": query_type,
            "created_at": "2024-01-15T12:00:00Z"
        }
        
        self.queries.append(query_record)
        return query_id
    
    async def get_query_history(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Mock query history retrieval"""
        return self.queries[skip:skip + limit]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Mock statistics"""
        return {
            "total_reports": len(self.reports),
            "total_queries": len(self.queries),
            "reports_by_ata_chapter": {"32": 1, "27": 1, "21": 1},
            "reports_by_severity": {"minor": 1, "major": 1, "moderate": 1}
        }
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "database_connection": "ok",
            "vector_extension": "ok",
            "total_reports": len(self.reports)
        }


async def test_prompt_templates():
    """Test prompt template functionality"""
    logger.info("Testing prompt templates...")
    
    try:
        from app.rag.prompt_templates import PromptTemplates
        
        templates = PromptTemplates()
        
        # Test query type detection
        test_cases = [
            ("What hydraulic problems exist?", "general"),
            ("Are there safety-critical issues?", "safety_critical"),
            ("What trends do you see in failures?", "trend_analysis"),
            ("Tell me about ATA Chapter 32", "ata_specific"),
            ("What defects are common?", "defect_analysis")
        ]
        
        for query, expected_type in test_cases:
            detected_type = templates.detect_query_type(query)
            logger.info(f"Query: '{query}' -> Type: {detected_type} (expected: {expected_type})")
            
            if detected_type != expected_type:
                logger.warning(f"Type detection mismatch for query: {query}")
        
        # Test context formatting
        context = templates.format_context_from_reports(SAMPLE_MAINTENANCE_REPORTS)
        assert len(context) > 0, "Context should not be empty"
        assert "Report 1:" in context, "Context should contain report markers"
        
        # Test source citations
        citations = templates.create_source_citations(SAMPLE_MAINTENANCE_REPORTS)
        assert len(citations) == len(SAMPLE_MAINTENANCE_REPORTS), "Should have citation for each report"
        
        logger.info("✅ Prompt templates test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Prompt templates test failed: {e}")
        return False


async def test_retriever():
    """Test retriever component"""
    logger.info("Testing retriever component...")
    
    try:
        from app.rag.retriever import Retriever
        
        # Create mock vector store
        mock_vector_store = MockVectorStore()
        
        # Create retriever
        retriever = Retriever(mock_vector_store)
        
        # Test basic retrieval
        results = await retriever.retrieve_relevant_reports(
            query="hydraulic leak",
            max_results=5,
            similarity_threshold=0.3
        )
        
        assert len(results) > 0, "Should find relevant reports"
        assert all("similarity_score" in r for r in results), "All results should have similarity scores"
        
        # Test ATA chapter filtering
        ata_results = await retriever.retrieve_by_ata_chapter(
            query="landing gear",
            ata_chapter="32",
            max_results=5
        )
        
        assert all(r["ata_chapter"] == "32" for r in ata_results), "Should only return Chapter 32 reports"
        
        # Test safety-critical retrieval
        safety_results = await retriever.retrieve_safety_critical(
            query="crack",
            max_results=5
        )
        
        # Should prioritize safety-critical reports
        safety_critical_count = sum(1 for r in safety_results if r.get("safety_critical") == "true")
        logger.info(f"Found {safety_critical_count} safety-critical reports")
        
        # Test health check
        health = await retriever.health_check()
        assert health["status"] == "healthy", "Retriever should be healthy"
        
        logger.info("✅ Retriever test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Retriever test failed: {e}")
        return False


async def test_generator():
    """Test generator component"""
    logger.info("Testing generator component...")
    
    try:
        from app.rag.generator import Generator
        
        # Create mock chat service
        mock_chat_service = MockChatService()
        
        # Create generator
        generator = Generator(mock_chat_service)
        
        # Test basic response generation
        response = await generator.generate_response(
            query="What hydraulic issues exist?",
            reports=SAMPLE_MAINTENANCE_REPORTS[:2],
            temperature=0.7
        )
        
        assert response["generation_successful"], "Generation should succeed"
        assert len(response["response"]) > 0, "Should generate non-empty response"
        assert len(response["sources"]) > 0, "Should include source citations"
        assert 0.0 <= response["confidence_score"] <= 1.0, "Confidence should be in valid range"
        
        # Test safety-critical response
        safety_response = await generator.generate_safety_critical_response(
            query="Are there any cracks?",
            reports=[SAMPLE_MAINTENANCE_REPORTS[1]]  # The crack report
        )
        
        assert safety_response["generation_successful"], "Safety generation should succeed"
        assert "safety_metadata" in safety_response, "Should include safety metadata"
        
        # Test trend analysis response
        trend_response = await generator.generate_trend_analysis_response(
            query="What trends do you see?",
            reports=SAMPLE_MAINTENANCE_REPORTS
        )
        
        assert trend_response["generation_successful"], "Trend generation should succeed"
        assert "trend_metadata" in trend_response, "Should include trend metadata"
        
        # Test no context response
        no_context_response = await generator.generate_response(
            query="What about engines?",
            reports=[],
            temperature=0.7
        )
        
        assert no_context_response["query_type"] == "no_context", "Should detect no context"
        assert no_context_response["confidence_score"] == 0.0, "No context should have zero confidence"
        
        # Test health check
        health = generator.health_check()
        assert health["status"] == "healthy", "Generator should be healthy"
        
        logger.info("✅ Generator test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Generator test failed: {e}")
        return False


async def test_rag_pipeline():
    """Test complete RAG pipeline"""
    logger.info("Testing RAG pipeline...")
    
    try:
        from app.rag.rag_pipeline import RAGPipeline
        from app.rag.retriever import Retriever
        from app.rag.generator import Generator
        
        # Create mock services
        mock_vector_store = MockVectorStore()
        mock_chat_service = MockChatService()
        
        # Create components
        retriever = Retriever(mock_vector_store)
        generator = Generator(mock_chat_service)
        
        # Create RAG pipeline
        rag_pipeline = RAGPipeline(retriever, generator, mock_vector_store)
        
        # Test standard query processing
        for test_query in SAMPLE_QUERIES:
            logger.info(f"Testing query: '{test_query['query']}'")
            
            response = await rag_pipeline.process_query(
                query=test_query["query"],
                max_results=5,
                similarity_threshold=0.3,
                temperature=0.7
            )
            
            assert response["generation_successful"], f"Query should succeed: {test_query['query']}"
            assert len(response["response"]) > 0, "Should generate response"
            assert "query_id" in response, "Should have query ID"
            assert "metadata" in response, "Should have metadata"
            
            logger.info(f"✅ Query processed successfully: {response['query_id']}")
        
        # Test safety-critical query
        safety_response = await rag_pipeline.process_safety_critical_query(
            query="Are there any dangerous cracks?",
            max_results=10
        )
        
        assert safety_response["generation_successful"], "Safety query should succeed"
        assert safety_response["safety_warning"], "Should have safety warning"
        
        # Test trend analysis query
        trend_response = await rag_pipeline.process_trend_analysis_query(
            query="What patterns do you see in failures?",
            max_results=20
        )
        
        assert trend_response["generation_successful"], "Trend query should succeed"
        assert "trend_metadata" in trend_response["metadata"], "Should have trend metadata"
        
        # Test ATA-specific query
        ata_response = await rag_pipeline.process_ata_specific_query(
            query="What problems exist?",
            ata_chapter="32",
            max_results=10
        )
        
        assert ata_response["generation_successful"], "ATA query should succeed"
        assert ata_response["metadata"]["ata_chapter"] == "32", "Should specify ATA chapter"
        
        # Test pipeline statistics
        stats = await rag_pipeline.get_pipeline_stats()
        assert "pipeline_status" in stats, "Should have pipeline status"
        assert "total_reports_available" in stats, "Should have report count"
        
        # Test health check
        health = await rag_pipeline.health_check()
        assert health["status"] == "healthy", "Pipeline should be healthy"
        assert "components" in health, "Should have component health"
        
        logger.info("✅ RAG pipeline test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG pipeline test failed: {e}")
        return False


async def test_streaming_query():
    """Test streaming query functionality"""
    logger.info("Testing streaming query...")
    
    try:
        from app.rag.rag_pipeline import RAGPipeline
        from app.rag.retriever import Retriever
        from app.rag.generator import Generator
        
        # Create mock services
        mock_vector_store = MockVectorStore()
        mock_chat_service = MockChatService()
        
        # Create components
        retriever = Retriever(mock_vector_store)
        generator = Generator(mock_chat_service)
        
        # Create RAG pipeline
        rag_pipeline = RAGPipeline(retriever, generator, mock_vector_store)
        
        # Test streaming query
        chunks = []
        async for chunk in rag_pipeline.process_streaming_query(
            query="What hydraulic problems exist?",
            max_results=5
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0, "Should generate streaming chunks"
        
        # Check for metadata and content chunks
        has_metadata = any(chunk.get("type") == "metadata" for chunk in chunks)
        has_content = any(chunk.get("type") == "content" for chunk in chunks)
        
        assert has_metadata, "Should have metadata chunk"
        assert has_content, "Should have content chunks"
        
        logger.info(f"✅ Streaming query test passed ({len(chunks)} chunks)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Streaming query test failed: {e}")
        return False


async def test_integration():
    """Test integration with main application components"""
    logger.info("Testing integration...")
    
    try:
        # Test imports
        from app.rag import RAGPipeline, Retriever, Generator, PromptTemplates
        from app.genai import GenAIClient, ChatService, ModelService
        
        logger.info("✅ All imports successful")
        
        # Test that components can be instantiated (with mocks)
        mock_embedding_service = MockEmbeddingService()
        mock_vector_store = MockVectorStore()
        mock_chat_service = MockChatService()
        
        # Test component creation
        templates = PromptTemplates()
        retriever = Retriever(mock_vector_store)
        generator = Generator(mock_chat_service)
        pipeline = RAGPipeline(retriever, generator, mock_vector_store)
        
        # Test basic functionality
        health = await pipeline.health_check()
        assert health["status"] == "healthy", "Integrated pipeline should be healthy"
        
        logger.info("✅ Integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False


async def run_all_tests():
    """Run all RAG pipeline tests"""
    logger.info("🚀 Starting RAG Pipeline Test Suite - Phase 5")
    logger.info("=" * 60)
    
    tests = [
        ("Prompt Templates", test_prompt_templates),
        ("Retriever Component", test_retriever),
        ("Generator Component", test_generator),
        ("RAG Pipeline", test_rag_pipeline),
        ("Streaming Query", test_streaming_query),
        ("Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} test...")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test_name:<25} {status}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    logger.info("-" * 60)
    logger.info(f"Total Tests: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {passed/len(results)*100:.1f}%")
    
    if failed == 0:
        logger.info("\n🎉 All RAG pipeline tests passed! Phase 5 implementation is ready.")
        return True
    else:
        logger.error(f"\n⚠️  {failed} test(s) failed. Please review and fix issues.")
        return False


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n✅ RAG Pipeline Test Suite completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ RAG Pipeline Test Suite failed!")
        sys.exit(1)
