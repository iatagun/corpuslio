"""API URL configuration."""

from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('documents/', views.documents_list, name='documents'),
    path('search/', views.search_corpus, name='search'),
    path('stats/<int:doc_id>/', views.document_stats, name='stats'),
    path('export/<int:doc_id>/', views.export_corpus, name='export'),
]
