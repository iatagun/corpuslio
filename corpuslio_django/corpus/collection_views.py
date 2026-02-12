"""Views for collection management."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .collections import Collection
from .models import Document


@login_required
def collections_view(request):
    """List all collections."""
    collections = Collection.objects.filter(owner=request.user)
    
    context = {
        'collections': collections,
        'active_tab': 'collections'
    }
    return render(request, 'corpus/collections.html', context)


@login_required
def collection_detail_view(request, coll_id):
    """View collection details."""
    collection = get_object_or_404(Collection, id=coll_id, owner=request.user)
    
    context = {
        'collection': collection,
        'documents': collection.documents.all(),
        'active_tab': 'collections'
    }
    return render(request, 'corpus/collection_detail.html', context)


@login_required
def create_collection_view(request):
    """Create new collection."""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        doc_ids = request.POST.getlist('documents')
        
        if not name:
            messages.error(request, '❌ Koleksiyon adı gereklidir.')
        elif not doc_ids:
            messages.error(request, '❌ En az bir belge seçilmelidir.')
        else:
            # Check if selected documents have at least 1 word total
            selected_docs = Document.objects.filter(id__in=doc_ids)
            total_words = sum(doc.get_word_count() for doc in selected_docs)
            
            if total_words == 0:
                messages.error(request, '❌ Seçilen belgeler en az 1 kelime içermelidir.')
            else:
                collection = Collection.objects.create(
                    name=name,
                    description=description
                )
                # assign ownership to the creating user
                collection.owner = request.user
                collection.save()
                collection.documents.set(selected_docs)
                
                messages.success(request, f'✅ "{name}" koleksiyonu oluşturuldu!')
                return redirect('corpus:collection_detail', coll_id=collection.id)
    
    documents = Document.objects.all()
    context = {
        'documents': documents,
        'active_tab': 'collections'
    }
    return render(request, 'corpus/create_collection.html', context)


@login_required
def edit_collection_view(request, coll_id):
    """Edit an existing collection (owner only)."""
    collection = get_object_or_404(Collection, id=coll_id)
    if collection.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Bu koleksiyonu düzenleme yetkiniz yok.')
        return redirect('corpus:collections')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        doc_ids = request.POST.getlist('documents')

        if not name:
            messages.error(request, '❌ Koleksiyon adı gereklidir.')
        elif not doc_ids:
            messages.error(request, '❌ En az bir belge seçilmelidir.')
        else:
            # Check if selected documents have at least 1 word total
            selected_docs = Document.objects.filter(id__in=doc_ids)
            total_words = sum(doc.get_word_count() for doc in selected_docs)
            
            if total_words == 0:
                messages.error(request, '❌ Seçilen belgeler en az 1 kelime içermelidir.')
            else:
                collection.name = name
                collection.description = description
                collection.save()
                collection.documents.set(selected_docs)
                messages.success(request, f'✅ "{name}" koleksiyonu güncellendi!')
                return redirect('corpus:collection_detail', coll_id=collection.id)

    documents = Document.objects.all()
    context = {
        'collection': collection,
        'documents': documents,
        'editing': True,
        'active_tab': 'collections'
    }
    return render(request, 'corpus/create_collection.html', context)


@login_required
def delete_collection_view(request, coll_id):
    """Delete a collection (owner only). Requires POST."""
    collection = get_object_or_404(Collection, id=coll_id)
    if collection.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Bu koleksiyonu silme yetkiniz yok.')
        return redirect('corpus:collections')

    if request.method == 'POST':
        name = collection.name
        collection.delete()
        messages.success(request, f'🗑️ "{name}" koleksiyonu silindi.')
        return redirect('corpus:collections')

    # If GET, show a simple confirmation page
    context = {'collection': collection, 'active_tab': 'collections'}
    return render(request, 'corpus/confirm_delete_collection.html', context)
