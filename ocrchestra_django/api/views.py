"""Django REST Framework API views."""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from corpus.models import Document
from corpus.services import CorpusService


@extend_schema(
    responses={200: {
        'type': 'object',
        'properties': {
            'count': {'type': 'integer'},
            'documents': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'filename': {'type': 'string'},
                        'format': {'type': 'string'},
                        'processed': {'type': 'boolean'},
                        'word_count': {'type': 'integer'}
                    }
                }
            }
        }
    }},
    description="İşlenmiş tüm dökümanları listeler"
)
@api_view(['GET'])
def documents_list(request):
    """List all documents."""
    documents = Document.objects.filter(processed=True)
    data = [
        {
            'id': doc.id,
            'filename': doc.filename,
            'format': doc.format,
            'processed': doc.processed,
            'word_count': doc.get_word_count()
        }
        for doc in documents
    ]
    
    return Response({'count': len(data), 'documents': data})


@extend_schema(
    request={
        'type': 'object',
        'properties': {
            'doc_id': {'type': 'integer'},
            'query': {'type': 'string'}
        },
        'required': ['doc_id']
    },
    responses={200: {
        'type': 'object',
        'properties': {
            'matches': {'type': 'integer'},
            'concordance': {'type': 'array', 'items': {'type': 'object'}}
        }
    }},
    description="Bir döküman içinde arama yapar"
)
@api_view(['POST'])
def search_corpus(request):
    """Search within a document."""
    doc_id = request.data.get('doc_id')
    
    if not doc_id:
        return Response({'error': 'doc_id required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        document = Document.objects.get(id=doc_id)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    
    service = CorpusService()
    results = service.search_in_document(document, request.data)
    
    return Response({
        'matches': len(results),
        'concordance': results
    })


@extend_schema(
    parameters=[
        OpenApiParameter(name='doc_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Döküman ID')
    ],
    responses={200: {
        'type': 'object',
        'properties': {
            'word_count': {'type': 'integer'},
            'unique_words': {'type': 'integer'},
            'average_word_length': {'type': 'number'}
        }
    }},
    description="Döküman istatistiklerini getirir"
)
@api_view(['GET'])
def document_stats(request, doc_id):
    """Get statistics for a document."""
    try:
        document = Document.objects.get(id=doc_id)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    
    service = CorpusService()
    stats = service.get_statistics(document)
    
    if stats is None:
        return Response({'error': 'Document not analyzed'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(stats)


@extend_schema(
    parameters=[
        OpenApiParameter(name='doc_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Döküman ID'),
        OpenApiParameter(name='format', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description='Export formatı (json, vrt, txt)')
    ],
    responses={200: {
        'type': 'object',
        'properties': {
            'format': {'type': 'string'},
            'content': {'type': 'string'}
        }
    }},
    description="Dökümanı belirtilen formatta export eder"
)
@api_view(['GET'])
def export_corpus(request, doc_id):
    """Export document in specified format."""
    try:
        document = Document.objects.get(id=doc_id)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    
    export_format = request.query_params.get('format', 'json')
    service = CorpusService()
    
    content = service.export_document(document, export_format=export_format)
    
    if content is None:
        return Response({'error': 'Export failed'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'format': export_format,
        'content': content
    })

