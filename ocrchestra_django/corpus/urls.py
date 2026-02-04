"""URL configuration for corpus app."""

from django.urls import path
from . import views
from . import analysis_views
from . import collection_views
from . import dashboard_views
from . import export_views

app_name = 'corpus'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Global search (AJAX endpoint)
    path('search/', views.global_search_view, name='global_search'),
    path('suggest/', views.search_suggestions_view, name='search_suggest'),
    
    # Main pages
    path('', views.home_view, name='home'),
    path('library/', views.library_view, name='library'),
    path('upload/', views.upload_view, name='upload'),
    path('analysis/<int:doc_id>/', views.analysis_view, name='analysis'),
    path('analysis/<int:doc_id>/download/', views.download_search_results, name='download_results'),
    path('ngrams/<int:doc_id>/', analysis_views.ngrams_view, name='ngrams'),
    path('wordcloud/<int:doc_id>/', analysis_views.wordcloud_view, name='wordcloud'),
    path('comparison/', analysis_views.comparison_view, name='comparison'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('collections/', collection_views.collections_view, name='collections'),
    path('collections/create/', collection_views.create_collection_view, name='create_collection'),
    path('collections/<int:coll_id>/', collection_views.collection_detail_view, name='collection_detail'),
    path('delete/<int:doc_id>/', views.delete_document, name='delete'),
    path('export/<int:doc_id>/', views.export_document, name='export'),
    path('task/<str:task_id>/', views.task_status_view, name='task_status'),
    
    # Advanced exports
    path('export/pdf/<int:doc_id>/', export_views.export_pdf_report, name='export_pdf'),
    path('export/excel/<int:doc_id>/', export_views.export_excel_statistics, name='export_excel'),
    path('export/csv/<int:doc_id>/', export_views.export_csv_data, name='export_csv'),
    
    # Tag management
    path('tags/add/<int:doc_id>/', views.add_tag_to_document, name='add_tag'),
    path('tags/remove/<int:doc_id>/<slug:tag_slug>/', views.remove_tag_from_document, name='remove_tag'),
    path('tags/bulk-add/', views.bulk_add_tags, name='bulk_add_tags'),
]
