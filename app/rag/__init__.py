"""
RAG (Retrieval-Augmented Generation) module for Boeing Aircraft Maintenance Report System

This module provides intelligent question-answering capabilities by combining:
1. Vector similarity search to retrieve relevant maintenance reports
2. Large language model generation to synthesize natural language responses
3. Source citation tracking for transparency and verification

Phase 5 Implementation - RAG Pipeline
"""

from .rag_pipeline import RAGPipeline
from .retriever import Retriever
from .generator import Generator
from .prompt_templates import PromptTemplates

__all__ = [
    'RAGPipeline',
    'Retriever', 
    'Generator',
    'PromptTemplates'
]

