"""Django REST Framework API views."""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from corpus.models import Document
from corpus.services import CorpusService


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
