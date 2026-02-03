"""Database Manager for OCRchestra.

Handles storage of documents, text content, and analysis results using SQLite.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session

logger = logging.getLogger(__name__)

Base = declarative_base()


class Document(Base):
    """Document model."""
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    format = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    
    # Relationships
    content = relationship("Content", back_populates="document", uselist=False, cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="document", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "format": self.format,
            "upload_date": self.upload_date,
            "processed": self.processed
        }


class Content(Base):
    """Text content model."""
    __tablename__ = 'content'

    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    raw_text = Column(Text)
    cleaned_text = Column(Text)

    document = relationship("Document", back_populates="content")


class Analysis(Base):
    """Linguistic analysis model."""
    __tablename__ = 'analysis'

    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    data = Column(Text)  # JSON blob of analysis

    document = relationship("Document", back_populates="analysis")

    def get_data(self) -> List[Dict[str, Any]]:
        """Return parsed JSON data."""
        if not self.data:
            return []
        try:
            return json.loads(self.data)
        except json.JSONDecodeError:
            return []


class DatabaseManager:
    """Manages database operations."""

    def __init__(self, db_path: str = "ocrchestra.db"):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def add_document(self, filename: str, format_type: str) -> Document:
        """Add a new document entry."""
        session = self.Session()
        new_doc = Document(filename=filename, format=format_type)
        session.add(new_doc)
        session.commit()
        session.refresh(new_doc)
        # Detach from session to allow usage outside
        session.expunge(new_doc)
        session.close()
        return new_doc

    def save_results(self, doc_id: int, raw_text: str, cleaned_text: str, analysis: List[Dict[str, Any]]):
        """Save processing results."""
        session = self.Session()
        doc = session.query(Document).get(doc_id)
        if not doc:
            session.close()
            raise ValueError(f"Document {doc_id} not found")

        # Create or update Content
        content = session.query(Content).filter_by(doc_id=doc_id).first()
        if not content:
            content = Content(doc_id=doc_id)
            session.add(content)
        content.raw_text = raw_text
        content.cleaned_text = cleaned_text

        # Create or update Analysis
        anl = session.query(Analysis).filter_by(doc_id=doc_id).first()
        if not anl:
            anl = Analysis(doc_id=doc_id)
            session.add(anl)
        anl.data = json.dumps(analysis, ensure_ascii=False)

        doc.processed = True
        session.commit()
        session.close()

    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get full document details."""
        session = self.Session()
        doc = session.query(Document).get(doc_id)
        if not doc:
            session.close()
            return None

        result = doc.to_dict()
        if doc.content:
            result["raw_text"] = doc.content.raw_text
            result["cleaned_text"] = doc.content.cleaned_text
        
        if doc.analysis:
            result["analysis"] = doc.analysis.get_data()
        else:
            result["analysis"] = []
            
        session.close()
        return result

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get list of all documents."""
        session = self.Session()
        docs = session.query(Document).order_by(Document.upload_date.desc()).all()
        result = [d.to_dict() for d in docs]
        session.close()
        return result

    def delete_document(self, doc_id: int):
        """Delete a document."""
        session = self.Session()
        doc = session.query(Document).get(doc_id)
        if doc:
            session.delete(doc)
            session.commit()
        session.close()
