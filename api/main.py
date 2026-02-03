"""FastAPI backend for OCRchestra corpus platform.

Provides REST API for:
- Search
- Statistics
- Export
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocrchestra.database_manager import DatabaseManager
from ocrchestra.search_engine import CorpusSearchEngine
from ocrchestra.statistics import CorpusStatistics
from ocrchestra.exporters import CorpusExporter

app = FastAPI(
    title="OCRchestra API",
    description="Turkish Corpus Analysis API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = DatabaseManager()


# Models
class SearchRequest(BaseModel):
    doc_id: int
    word_pattern: Optional[str] = None
    lemma: Optional[str] = None
    pos_tags: Optional[List[str]] = None
    min_confidence: float = 0.0
    max_confidence: float = 1.0
    regex: bool = False
    case_sensitive: bool = False
    context_words: int = 5


class SearchResponse(BaseModel):
    matches: int
    concordance: List[Dict[str, Any]]


# API Endpoints

@app.get("/")
def root():
    """API root."""
    return {
        "name": "OCRchestra API",
        "version": "1.0.0",
        "endpoints": {
            "/docs": "API documentation",
            "/search": "Search corpus",
            "/stats/{doc_id}": "Get statistics",
            "/export/{doc_id}": "Export corpus"
        }
    }


@app.post("/search", response_model=SearchResponse)
def search_corpus(request: SearchRequest):
    """Search corpus with filters.
    
    Args:
        request: Search parameters
    
    Returns:
        Search results with concordance
    """
    try:
        search_engine = CorpusSearchEngine(db)
        
        # Execute search
        matches = search_engine.complex_query(
            doc_id=request.doc_id,
            word_pattern=request.word_pattern,
            lemma=request.lemma,
            pos_tags=request.pos_tags,
            min_confidence=request.min_confidence,
            max_confidence=request.max_confidence,
            regex=request.regex,
            case_sensitive=request.case_sensitive
        )
        
        # Get concordance
        concordance = search_engine.get_concordance(
            matches,
            doc_id=request.doc_id,
            context_words=request.context_words
        )
        
        return SearchResponse(
            matches=len(concordance),
            concordance=concordance
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/{doc_id}")
def get_statistics(doc_id: int):
    """Get corpus statistics.
    
    Args:
        doc_id: Document ID
    
    Returns:
        Statistics dictionary
    """
    try:
        doc = db.get_document(doc_id)
        
        if not doc or not doc.get('analysis'):
            raise HTTPException(status_code=404, detail="Document not found or not analyzed")
        
        stats = CorpusStatistics(doc['analysis'])
        
        return {
            "token_count": stats.token_count(),
            "type_count": stats.type_count(),
            "ttr": stats.type_token_ratio(),
            "word_frequency": stats.word_frequency(top_n=50),
            "lemma_frequency": stats.lemma_frequency(top_n=50),
            "pos_distribution": stats.pos_distribution(),
            "zipf": stats.zipf_distribution()[:20]  # Top 20
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export/{doc_id}")
def export_corpus(
    doc_id: int,
    format: str = Query("json", regex="^(json|csv|conllu|vrt)$")
):
    """Export corpus in specified format.
    
    Args:
        doc_id: Document ID
        format: Export format (json, csv, conllu, vrt)
    
    Returns:
        Exported data
    """
    try:
        doc = db.get_document(doc_id)
        
        if not doc or not doc.get('analysis'):
            raise HTTPException(status_code=404, detail="Document not found or not analyzed")
        
        metadata = {
            'filename': doc.get('filename'),
            'doc_id': doc_id,
            'format': doc.get('format')
        }
        
        exporter = CorpusExporter(doc['analysis'], metadata)
        
        if format == "json":
            return {"data": exporter.to_json(pretty=True), "content_type": "application/json"}
        elif format == "csv":
            return {"data": exporter.to_csv(), "content_type": "text/csv"}
        elif format == "conllu":
            return {"data": exporter.to_conllu(), "content_type": "text/plain"}
        elif format == "vrt":
            return {"data": exporter.to_vrt(), "content_type": "text/xml"}
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
def list_documents():
    """List all documents in corpus.
    
    Returns:
        List of documents
    """
    try:
        docs = db.get_all_documents()
        return {
            "count": len(docs),
            "documents": [
                {
                    "id": d['id'],
                    "filename": d['filename'],
                    "format": d['format'],
                    "processed": d['processed']
                }
                for d in docs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
