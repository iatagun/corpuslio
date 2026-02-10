"""DRF serializers for Corpus API."""

from rest_framework import serializers
from corpus.models import Document, UserProfile, Tag
from .models import APIKey
from drf_spectacular.utils import extend_schema_field, OpenApiTypes


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    
    # `uploaded_by` was removed from Document model; expose filename instead
    word_count = serializers.IntegerField(source='get_word_count', read_only=True)
    tags = serializers.StringRelatedField(many=True, read_only=True)
    privacy_status_display = serializers.CharField(source='get_privacy_status_display', read_only=True)
    text_type_display = serializers.CharField(source='get_text_type_display', read_only=True)
    license_display = serializers.CharField(source='get_license_display', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'filename', 'author', 'genre', 'upload_date',
            'word_count', 'tags', 'publication_year', 'language',
            # Week 5: Corpus metadata
            'text_type', 'text_type_display', 'license', 'license_display',
            'region', 'collection', 'token_count', 'document_date',
            # Week 6: Privacy
            'privacy_status', 'privacy_status_display', 'contains_personal_data',
            # CoNLL-U
            # expose whether analysis has dependencies via related Analysis model (in detail serializer)
        ]
        read_only_fields = ['id', 'uploaded_at', 'word_count', 'token_count']


class DocumentDetailSerializer(DocumentSerializer):
    """Detailed serializer with content (for authenticated users)."""
    
    raw_text = serializers.SerializerMethodField()
    cleaned_text = serializers.SerializerMethodField()
    
    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + ['raw_text', 'cleaned_text', 'has_dependencies']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_raw_text(self, obj) -> str:
        """Get raw text if user has permission."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, 'content') and obj.content:
                return obj.content.raw_text[:1000]  # Limit to 1000 chars in API
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_cleaned_text(self, obj) -> str:
        """Get cleaned text if user has permission."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(obj, 'content') and obj.content:
                return obj.content.cleaned_text[:1000]  # Limit to 1000 chars
        return None

    has_dependencies = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_has_dependencies(self, obj) -> bool:
        return bool(getattr(getattr(obj, 'analysis', None), 'has_dependencies', False))


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    
    document_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'document_count']


class SearchResultSerializer(serializers.Serializer):
    """Serializer for search/concordance results."""
    
    document_id = serializers.IntegerField()
    document_title = serializers.CharField()
    sentence = serializers.CharField()
    left_context = serializers.CharField()
    keyword = serializers.CharField()
    right_context = serializers.CharField()
    position = serializers.IntegerField()


class FrequencySerializer(serializers.Serializer):
    """Serializer for word/lemma frequency results."""
    
    word = serializers.CharField()
    frequency = serializers.IntegerField()
    relative_frequency = serializers.FloatField(required=False)
    documents = serializers.IntegerField(required=False)


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for API Key model."""
    
    user = serializers.StringRelatedField(read_only=True)
    daily_limit = serializers.IntegerField(source='get_daily_limit', read_only=True)
    remaining_quota = serializers.SerializerMethodField()
    
    class Meta:
        model = APIKey
        fields = [
            'id', 'user', 'name', 'key', 'tier', 
            'requests_today', 'daily_limit', 'remaining_quota',
            'total_requests', 'last_request', 
            'is_active', 'created_at', 'expires_at'
        ]
        read_only_fields = ['key', 'requests_today', 'total_requests', 'last_request']
        extra_kwargs = {
            'key': {'write_only': False}  # Show key only on creation
        }
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_remaining_quota(self, obj) -> str:
        """Calculate remaining quota for today."""
        limit = obj.get_daily_limit()
        if limit == float('inf'):
            return 'unlimited'
        return max(0, limit - obj.requests_today)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for User Profile."""
    
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'role', 'role_display',
            'institution', 'daily_export_limit', 'monthly_query_limit',
            'can_use_api', 'is_verified'
        ]
        read_only_fields = [
            'role', 'daily_export_limit', 'monthly_query_limit',
            'can_use_api', 'is_verified'
        ]
