"""Prompt templates for RAG-powered maintenance report queries."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptTemplates:
    """Collection of prompt templates for different query types."""
    
    # Base system prompt for maintenance report queries
    SYSTEM_PROMPT = """You are an expert aircraft maintenance analyst with deep knowledge of Boeing aircraft systems, ATA (Air Transport Association) specifications, and iSpec 2200 standards.

Your role is to analyze maintenance reports and provide accurate, helpful responses to questions about aircraft maintenance issues, procedures, and safety concerns.

Key guidelines:
1. Base your responses primarily on the provided maintenance report context
2. Use your aviation expertise to interpret technical details and provide insights
3. Always cite specific reports when referencing information
4. If information is not available in the context, clearly state this limitation
5. Prioritize safety-critical issues and provide appropriate warnings when relevant
6. Use proper aviation terminology and ATA chapter references
7. Be concise but thorough in your explanations

When referencing maintenance reports, use this format: [Report ID: aircraft_model - ATA_chapter]"""

    # Template for general maintenance queries
    GENERAL_QUERY_TEMPLATE = """Based on the following maintenance reports, please answer the user's question:

MAINTENANCE REPORTS:
{context}

USER QUESTION: {query}

Please provide a comprehensive answer based on the maintenance reports above. Include relevant details about:
- Specific aircraft models and ATA chapters involved
- Types of defects or issues found
- Maintenance actions taken
- Any safety implications
- Patterns or trends if multiple reports are relevant

If the reports don't contain sufficient information to fully answer the question, please state what information is missing."""

    # Template for defect analysis queries
    DEFECT_ANALYSIS_TEMPLATE = """Analyze the following maintenance reports to answer questions about defects and maintenance issues:

MAINTENANCE REPORTS:
{context}

USER QUESTION: {query}

Please provide a detailed analysis including:
- Types of defects identified (corrosion, cracks, wear, etc.)
- Affected aircraft systems and components
- Root cause analysis if evident from the reports
- Maintenance actions performed
- Preventive measures or recommendations
- Safety criticality assessment

Focus on technical accuracy and practical maintenance insights."""

    # Template for ATA chapter specific queries
    ATA_SPECIFIC_TEMPLATE = """The following maintenance reports are related to ATA Chapter {ata_chapter} ({ata_chapter_name}):

MAINTENANCE REPORTS:
{context}

USER QUESTION: {query}

Please provide a focused analysis of this ATA chapter's maintenance issues including:
- Common problems in this system
- Maintenance procedures and best practices
- Component reliability patterns
- Safety considerations specific to this system
- Regulatory compliance aspects if relevant

Ensure your response is specific to the {ata_chapter_name} system."""

    # Template for trend analysis queries
    TREND_ANALYSIS_TEMPLATE = """Analyze trends and patterns in the following maintenance reports:

MAINTENANCE REPORTS:
{context}

USER QUESTION: {query}

Please identify and analyze:
- Recurring issues or failure patterns
- Aircraft models most affected
- Seasonal or operational trends if evident
- Component reliability trends
- Maintenance effectiveness indicators
- Recommendations for preventive actions

Provide statistical insights where possible and highlight any concerning trends."""

    # Template for safety-critical queries
    SAFETY_CRITICAL_TEMPLATE = """⚠️ SAFETY-CRITICAL ANALYSIS ⚠️

The following maintenance reports contain safety-critical information:

MAINTENANCE REPORTS:
{context}

USER QUESTION: {query}

Please provide a safety-focused analysis including:
- Immediate safety implications
- Risk assessment based on the reports
- Regulatory compliance considerations
- Required follow-up actions
- Fleet-wide implications if applicable
- Emergency procedures if relevant

⚠️ This analysis is for informational purposes only. Always follow official maintenance procedures and consult with certified maintenance personnel for safety-critical decisions."""

    def __init__(self):
        """Initialize prompt templates."""
        logger.info("Initialized PromptTemplates")
    
    def get_system_prompt(self) -> str:
        """Get the base system prompt.
        
        Returns:
            System prompt string
        """
        return self.SYSTEM_PROMPT
    
    def format_general_query(self, query: str, context: str) -> str:
        """Format a general maintenance query prompt.
        
        Args:
            query: User's question
            context: Maintenance reports context
            
        Returns:
            Formatted prompt string
        """
        return self.GENERAL_QUERY_TEMPLATE.format(
            query=query,
            context=context
        )
    
    def format_defect_analysis(self, query: str, context: str) -> str:
        """Format a defect analysis query prompt.
        
        Args:
            query: User's question about defects
            context: Maintenance reports context
            
        Returns:
            Formatted prompt string
        """
        return self.DEFECT_ANALYSIS_TEMPLATE.format(
            query=query,
            context=context
        )
    
    def format_ata_specific_query(self, query: str, context: str, 
                                 ata_chapter: str, ata_chapter_name: str) -> str:
        """Format an ATA chapter specific query prompt.
        
        Args:
            query: User's question
            context: Maintenance reports context
            ata_chapter: ATA chapter number
            ata_chapter_name: ATA chapter name
            
        Returns:
            Formatted prompt string
        """
        return self.ATA_SPECIFIC_TEMPLATE.format(
            query=query,
            context=context,
            ata_chapter=ata_chapter,
            ata_chapter_name=ata_chapter_name
        )
    
    def format_trend_analysis(self, query: str, context: str) -> str:
        """Format a trend analysis query prompt.
        
        Args:
            query: User's question about trends
            context: Maintenance reports context
            
        Returns:
            Formatted prompt string
        """
        return self.TREND_ANALYSIS_TEMPLATE.format(
            query=query,
            context=context
        )
    
    def format_safety_critical_query(self, query: str, context: str) -> str:
        """Format a safety-critical query prompt.
        
        Args:
            query: User's safety-related question
            context: Maintenance reports context
            
        Returns:
            Formatted prompt string
        """
        return self.SAFETY_CRITICAL_TEMPLATE.format(
            query=query,
            context=context
        )
    
    def format_context_from_reports(self, reports: List[Dict[str, Any]]) -> str:
        """Format maintenance reports into context string.
        
        Args:
            reports: List of maintenance report dictionaries
            
        Returns:
            Formatted context string
        """
        if not reports:
            return "No relevant maintenance reports found."
        
        context_parts = []
        
        for i, report in enumerate(reports, 1):
            # Extract key information
            report_id = report.get('id', 'Unknown')
            aircraft_model = report.get('aircraft_model', 'Unknown Aircraft')
            ata_chapter = report.get('ata_chapter', 'Unknown')
            ata_chapter_name = report.get('ata_chapter_name', 'Unknown System')
            report_text = report.get('report_text', '')
            defect_types = report.get('defect_types', [])
            severity = report.get('severity', 'Unknown')
            safety_critical = report.get('safety_critical', 'false')
            similarity_score = report.get('similarity_score', 0.0)
            
            # Format individual report
            context_part = f"""
Report {i}:
- ID: {report_id}
- Aircraft: {aircraft_model}
- ATA Chapter: {ata_chapter} ({ata_chapter_name})
- Defect Types: {', '.join(defect_types) if defect_types else 'None specified'}
- Severity: {severity}
- Safety Critical: {safety_critical}
- Relevance Score: {similarity_score:.3f}

Report Content:
{report_text}
"""
            context_parts.append(context_part.strip())
        
        return "\n\n" + "="*50 + "\n\n".join(context_parts)
    
    def detect_query_type(self, query: str) -> str:
        """Detect the type of query to select appropriate template.
        
        Args:
            query: User's question
            
        Returns:
            Query type string
        """
        query_lower = query.lower()
        
        # Safety-critical keywords
        safety_keywords = [
            'safety', 'critical', 'emergency', 'dangerous', 'risk', 'hazard',
            'accident', 'incident', 'failure', 'malfunction', 'urgent'
        ]
        
        # Defect analysis keywords
        defect_keywords = [
            'defect', 'crack', 'corrosion', 'wear', 'damage', 'leak', 'break',
            'fault', 'problem', 'issue', 'failure', 'deterioration'
        ]
        
        # Trend analysis keywords
        trend_keywords = [
            'trend', 'pattern', 'recurring', 'frequent', 'common', 'statistics',
            'analysis', 'compare', 'over time', 'history', 'multiple'
        ]
        
        # ATA chapter keywords (check for specific chapter references)
        ata_keywords = ['ata', 'chapter', 'system']
        
        # Check for safety-critical queries first (highest priority)
        if any(keyword in query_lower for keyword in safety_keywords):
            return 'safety_critical'
        
        # Check for trend analysis
        elif any(keyword in query_lower for keyword in trend_keywords):
            return 'trend_analysis'
        
        # Check for defect analysis
        elif any(keyword in query_lower for keyword in defect_keywords):
            return 'defect_analysis'
        
        # Check for ATA-specific queries
        elif any(keyword in query_lower for keyword in ata_keywords):
            return 'ata_specific'
        
        # Default to general query
        else:
            return 'general'
    
    def select_template(self, query: str, context: str, 
                       reports: List[Dict[str, Any]]) -> str:
        """Select and format the appropriate template based on query type.
        
        Args:
            query: User's question
            context: Formatted context string
            reports: List of source reports
            
        Returns:
            Formatted prompt string
        """
        query_type = self.detect_query_type(query)
        
        if query_type == 'safety_critical':
            return self.format_safety_critical_query(query, context)
        
        elif query_type == 'trend_analysis':
            return self.format_trend_analysis(query, context)
        
        elif query_type == 'defect_analysis':
            return self.format_defect_analysis(query, context)
        
        elif query_type == 'ata_specific':
            # Try to extract ATA chapter from reports
            ata_chapter = None
            ata_chapter_name = None
            
            for report in reports:
                if report.get('ata_chapter') and report.get('ata_chapter_name'):
                    ata_chapter = report['ata_chapter']
                    ata_chapter_name = report['ata_chapter_name']
                    break
            
            if ata_chapter and ata_chapter_name:
                return self.format_ata_specific_query(query, context, ata_chapter, ata_chapter_name)
            else:
                return self.format_general_query(query, context)
        
        else:  # general query
            return self.format_general_query(query, context)
    
    def create_source_citations(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create source citations from reports.
        
        Args:
            reports: List of maintenance report dictionaries
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        for report in reports:
            citation = {
                'report_id': report.get('id', 'Unknown'),
                'aircraft_model': report.get('aircraft_model', 'Unknown'),
                'ata_chapter': report.get('ata_chapter', 'Unknown'),
                'ata_chapter_name': report.get('ata_chapter_name', 'Unknown'),
                'similarity_score': report.get('similarity_score', 0.0),
                'excerpt': self._create_excerpt(report.get('report_text', '')),
                'defect_types': report.get('defect_types', []),
                'severity': report.get('severity', 'Unknown'),
                'safety_critical': report.get('safety_critical', 'false')
            }
            citations.append(citation)
        
        return citations
    
    def _create_excerpt(self, text: str, max_length: int = 200) -> str:
        """Create a brief excerpt from report text.
        
        Args:
            text: Full report text
            max_length: Maximum excerpt length
            
        Returns:
            Excerpt string
        """
        if not text:
            return "No content available"
        
        if len(text) <= max_length:
            return text
        
        # Find a good breaking point near the max length
        excerpt = text[:max_length]
        last_space = excerpt.rfind(' ')
        
        if last_space > max_length * 0.8:  # If we found a space in the last 20%
            excerpt = excerpt[:last_space]
        
        return excerpt + "..."

