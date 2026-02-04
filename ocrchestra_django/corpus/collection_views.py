"""Views for collection management."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .collections import Collection
from .models import Document


def collections_view(request):
    """List all collections."""
    collections = Collection.objects.all()
    
    context = {
        'collections': collections,
        'active_tab': 'collections'
    }
    return render(request, 'corpus/collections.html', context)


def collection_detail_view(request, coll_id):
    """View collection details."""
    collection = get_object_or_404(Collection, id=coll_id)
    
    context = {
        'collection': collection,
        'documents': collection.documents.all(),
        'active_tab': 'collections'
    }
    return render(request, 'corpus/collection_detail.html', context)


def create_collection_view(request):
    """Create new collection."""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        doc_ids = request.POST.getlist('documents')
        
        if name:
            collection = Collection.objects.create(
                name=name,
                description=description
            )
            
            if doc_ids:
                collection.documents.set(Document.objects.filter(id__in=doc_ids))
            
            messages.success(request, f'✅ "{name}" koleksiyonu oluşturuldu!')
            return redirect('corpus:collection_detail', coll_id=collection.id)
        else:
            messages.error(request, '❌ Koleksiyon adı gereklidir.')
    
    documents = Document.objects.all()
    context = {
        'documents': documents,
        'active_tab': 'collections'
    }
    return render(request, 'corpus/create_collection.html', context)
