"""URL configuration for corpus app."""

from django.urls import path
from . import views
from . import analysis_views
from . import collection_views
from . import dashboard_views

app_name = 'corpus'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('library/', views.library_view, name='library'),
    path('upload/', views.upload_view, name='upload'),
    path('analysis/<int:doc_id>/', views.analysis_view, name='analysis'),
    path('analysis/<int:doc_id>/download/', views.download_search_results, name='download_results'),
    path('ngrams/<int:doc_id>/', analysis_views.ngrams_view, name='ngrams'),
    path('wordcloud/<int:doc_id>/', analysis_views.wordcloud_view, name='wordcloud'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('collections/', collection_views.collections_view, name='collections'),
    path('collections/create/', collection_views.create_collection_view, name='create_collection'),
    path('collections/<int:coll_id>/', collection_views.collection_detail_view, name='collection_detail'),
    path('delete/<int:doc_id>/', views.delete_document, name='delete'),
    path('export/<int:doc_id>/', views.export_document, name='export'),
    path('task/<str:task_id>/', views.task_status_view, name='task_status'),
]
