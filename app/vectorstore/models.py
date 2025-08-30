"""SQLAlchemy models with pgvector support for maintenance reports."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, String, Text, JSON, func, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class MaintenanceReport(Base):
    """Maintenance report with vector embedding storage."""
    
    __tablename__ = "maintenance_reports"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Report content
    report_text = Column(Text, nullable=False)
    aircraft_model = Column(String(100))
    report_date = Column(DateTime)
    
    # Classification results from Phase 3
    ata_chapter = Column(String(10))
    ata_chapter_name = Column(String(200))
    ispec_parts = Column(ARRAY(String))
    defect_types = Column(ARRAY(String))
    maintenance_actions = Column(ARRAY(String))
    severity = Column(String(20))
    safety_critical = Column(String(10))  # Store as string for JSON compatibility
    confidence_score = Column(String(10))  # Store as string for JSON compatibility
    
    # Vector embedding (1536 dimensions for OpenAI text-embedding-ada-002)
    embedding = Column(Vector(1536))
    
    # Classification metadata
    classification_metadata = Column(JSON)
    processing_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_maintenance_reports_ata_chapter', 'ata_chapter'),
        Index('ix_maintenance_reports_severity', 'severity'),
        Index('ix_maintenance_reports_created_at', 'created_at'),
        Index('ix_maintenance_reports_embedding_cosine', 'embedding', 
              postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'report_text': self.report_text,
            'aircraft_model': self.aircraft_model,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'ata_chapter': self.ata_chapter,
            'ata_chapter_name': self.ata_chapter_name,
            'ispec_parts': self.ispec_parts or [],
            'defect_types': self.defect_types or [],
            'maintenance_actions': self.maintenance_actions or [],
            'severity': self.severity,
            'safety_critical': self.safety_critical == 'true' if self.safety_critical else False,
            'confidence_score': float(self.confidence_score) if self.confidence_score else 0.0,
            'classification_metadata': self.classification_metadata or {},
            'processing_notes': self.processing_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class QueryHistory(Base):
    """Query history with vector embedding and response tracking."""
    
    __tablename__ = "query_history"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Query content
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1536))
    
    # Response data
    response_text = Column(Text)
    sources = Column(JSON)  # List of source report IDs and relevance scores
    
    # Query metadata
    query_type = Column(String(50))  # natural_language, structured, etc.
    processing_time_ms = Column(String(10))  # Store as string for JSON compatibility
    
    # User feedback
    feedback_rating = Column(String(10))  # Store as string for JSON compatibility
    feedback_text = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('ix_query_history_created_at', 'created_at'),
        Index('ix_query_history_query_type', 'query_type'),
        Index('ix_query_history_embedding_cosine', 'query_embedding', 
              postgresql_using='ivfflat', postgresql_ops={'query_embedding': 'vector_cosine_ops'}),
    )
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            'id': str(self.id),
            'query_text': self.query_text,
            'response_text': self.response_text,
            'sources': self.sources or [],
            'query_type': self.query_type,
            'processing_time_ms': int(self.processing_time_ms) if self.processing_time_ms else 0,
            'feedback_rating': int(self.feedback_rating) if self.feedback_rating else None,
            'feedback_text': self.feedback_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


def create_tables(engine):
    """Create all tables. This should be run during application startup."""
    Base.metadata.create_all(bind=engine)