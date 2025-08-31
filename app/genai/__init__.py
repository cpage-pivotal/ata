"""
GenAI integration module for Boeing Aircraft Maintenance Report System

This module provides integration with GenAI on Tanzu Platform services:
1. OpenAI-compatible client setup for chat completions
2. Model discovery and selection
3. Chat completion wrapper with error handling
4. Service health monitoring

Phase 5 Implementation - GenAI Integration
"""

from .client import GenAIClient
from .chat import ChatService
from .models import ModelService

__all__ = [
    'GenAIClient',
    'ChatService', 
    'ModelService'
]

