"""API ViewSets for Corpus Platform."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Count, Q
from django.core.cache import cache
from collections import Counter

from corpus.models import Document, Tag
from .models import APIKey
from .serializers import (
    DocumentSerializer, DocumentDetailSerializer, TagSerializer,
    SearchResultSerializer, FrequencySerializer, APIKeySerializer
)
from .throttling import APIKeyRateThrottle, SearchThrottle, ExportThrottle


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for browsing and searching documents.
    
    list: Get all documents (filterable by metadata)
    retrieve: Get specific document details
    search: Full-text search across documents
    """
    
    queryset = Document.objects.all().select_related('content', 'analysis').prefetch_related('tags')
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [APIKeyRateThrottle]
    
    filterset_fields = ['genre', 'author', 'publication_year', 'language', 'text_type', 'license', 'collection', 'privacy_status']
    search_fields = ['filename', 'author', 'genre']
    ordering_fields = ['upload_date', 'filename', 'publication_year', 'word_count']
    ordering = ['-upload_date']
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return DocumentDetailSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        """Filter queryset based on privacy and permissions."""
        queryset = super().get_queryset()
        
        # Only show public/anonymized documents to non-authenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(privacy_status='public') | Q(privacy_status='anonymized')
            )
        # Authenticated users see everything (no uploader field available)
        
        return queryset
    
    @action(detail=False, methods=['get'], throttle_classes=[SearchThrottle])
    def search(self, request):
        """
        Full-text search across documents.
        
        Parameters:
        - q: Search query (required)
        - context: Number of words for context (default: 5)
        - limit: Max results (default: 100, max: 1000)
        """
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({'error': 'Query parameter "q" is required'}, status=400)
        
        try:
            context_size = int(request.query_params.get('context', 5))
            limit = min(int(request.query_params.get('limit', 100)), 1000)
        except ValueError:
            return Response({'error': 'Invalid context or limit parameter'}, status=400)
        
        # Search in document content
        documents = self.get_queryset().filter(
            content__cleaned_text__icontains=query
        ).select_related('content')[:limit]
        
        results = []
        for doc in documents:
            text = doc.content.cleaned_text if hasattr(doc, 'content') and doc.content else ''
            
            # Simple concordance extraction
            words = text.split()
            for i, word in enumerate(words):
                if query.lower() in word.lower():
                    left = ' '.join(words[max(0, i - context_size):i])
                    right = ' '.join(words[i + 1:i + context_size + 1])
                    
                    results.append({
                        'document_id': doc.id,
                        'document_title': doc.filename,
                        'left_context': left,
                        'keyword': word,
                        'right_context': right,
                        'position': i,
                        'sentence': f"{left} {word} {right}"
                    })
        
        serializer = SearchResultSerializer(results[:limit], many=True)
        return Response({
            'query': query,
            'total_results': len(results),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def frequency(self, request, pk=None):
        """
        Get word frequency list for a document.
        
        Parameters:
        - limit: Max words to return (default: 100, max: 1000)
        - min_freq: Minimum frequency (default: 1)
        """
        document = self.get_object()
        
        if not hasattr(document, 'content') or not document.content:
            return Response({'error': 'Document has no text content'}, status=404)
        
        try:
            limit = min(int(request.query_params.get('limit', 100)), 1000)
            min_freq = int(request.query_params.get('min_freq', 1))
        except ValueError:
            return Response({'error': 'Invalid limit or min_freq parameter'}, status=400)
        
        # Cache key
        cache_key = f'freq_{document.id}_{min_freq}'
        frequency_data = cache.get(cache_key)
        
        if not frequency_data:
            text = document.content.cleaned_text or ''
            words = [w.lower() for w in text.split() if w.isalpha()]
            
            word_counts = Counter(words)
            total_words = len(words)
            
            frequency_data = [
                {
                    'word': word,
                    'frequency': count,
                    'relative_frequency': round(count / total_words * 1000000, 2)  # Per million
                }
                for word, count in word_counts.most_common()
                if count >= min_freq
            ][:limit]
            
            # Cache for 1 hour
            cache.set(cache_key, frequency_data, 3600)
        
        serializer = FrequencySerializer(frequency_data, many=True)
        return Response({
            'document_id': document.id,
            'document_title': document.filename,
            'total_words': sum(item['frequency'] for item in frequency_data),
            'unique_words': len(frequency_data),
            'frequencies': serializer.data
        })


class GlobalFrequencyViewSet(viewsets.ViewSet):
    """
    Global frequency lists across entire corpus or filtered subset.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = FrequencySerializer
    throttle_classes = [APIKeyRateThrottle]
    
    def list(self, request):
        """
        Get global word frequency across corpus.
        
        Parameters:
        - genre: Filter by genre (optional)
        - collection: Filter by collection (optional)
        - limit: Max words to return (default: 100, max: 5000)
        - min_freq: Minimum frequency (default: 2)
        """
        try:
            limit = min(int(request.query_params.get('limit', 100)), 5000)
            min_freq = int(request.query_params.get('min_freq', 2))
        except ValueError:
            return Response({'error': 'Invalid limit or min_freq parameter'}, status=400)
        
        genre = request.query_params.get('genre')
        collection = request.query_params.get('collection')
        
        # Build cache key
        cache_key = f'global_freq_{genre}_{collection}_{min_freq}'
        frequency_data = cache.get(cache_key)
        
        if not frequency_data:
            # Query documents
            queryset = Document.objects.filter(
                privacy_status__in=['public', 'anonymized']
            ).select_related('content')
            
            if genre:
                queryset = queryset.filter(genre=genre)
            if collection:
                queryset = queryset.filter(collection=collection)
            
            # Aggregate word frequencies
            all_words = []
            doc_count = {}
            
            for doc in queryset:
                if hasattr(doc, 'content') and doc.content and doc.content.cleaned_text:
                    words = [w.lower() for w in doc.content.cleaned_text.split() if w.isalpha()]
                    all_words.extend(words)
                    
                    # Track document frequency
                    for word in set(words):
                        doc_count[word] = doc_count.get(word, 0) + 1
            
            word_counts = Counter(all_words)
            total_words = len(all_words)
            
            frequency_data = [
                {
                    'word': word,
                    'frequency': count,
                    'relative_frequency': round(count / total_words * 1000000, 2),
                    'documents': doc_count.get(word, 0)
                }
                for word, count in word_counts.most_common()
                if count >= min_freq
            ][:limit]
            
            # Cache for 6 hours
            cache.set(cache_key, frequency_data, 21600)
        
        serializer = FrequencySerializer(frequency_data, many=True)
        return Response({
            'filters': {
                'genre': genre,
                'collection': collection,
                'min_freq': min_freq
            },
            'total_unique_words': len(frequency_data),
            'frequencies': serializer.data
        })


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for browsing tags."""
    
    queryset = Tag.objects.annotate(document_count=Count('documents')).order_by('-document_count')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [APIKeyRateThrottle]


class APIKeyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing API keys.
    Users can only see/manage their own keys.
    """
    
    serializer_class = APIKeySerializer
    # Provide a base queryset to help schema generation; access is restricted by get_queryset
    queryset = APIKey.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own API keys."""
        return APIKey.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically set user when creating API key."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate API key."""
        api_key = self.get_object()
        api_key.key = APIKey.generate_key()
        api_key.save()
        
        serializer = self.get_serializer(api_key)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reset_quota(self, request, pk=None):
        """Reset daily quota counter (admin only)."""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=403)
        
        api_key = self.get_object()
        api_key.reset_daily_counter()
        
        serializer = self.get_serializer(api_key)
        return Response(serializer.data)
