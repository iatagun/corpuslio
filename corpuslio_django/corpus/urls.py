"""URL configuration for corpus app."""

from django.urls import path
from . import views
from . import analysis_views
from . import collection_views
from . import dashboard_views
from . import export_views
from . import dependency_views
from . import statistics_views
from . import privacy_views
from . import advanced_search_views
from . import gdpr_views  # Week 11: KVKK/GDPR compliance
from . import search_views  # Corpus Query Platform search views

app_name = 'corpus'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/login-history/', views.login_history_view, name='login_history'),  # Task 11.15
    path('profile/watermark-preference/', views.update_watermark_preference, name='update_watermark_preference'),  # Watermark preference toggle
    
    # Email Verification (Task 11.6)
    path('auth/verification-sent/', views.email_verification_sent_view, name='verification_sent'),
    path('auth/verify-email/<str:token>/', views.email_verify_view, name='verify_email'),
    path('auth/resend-verification/', views.resend_verification_view, name='resend_verification'),
    
    # Password Reset (Task 11.12)
    path('auth/password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('auth/password-reset-sent/', views.password_reset_sent_view, name='password_reset_sent'),
    path('auth/reset/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # Global search (AJAX endpoint)
    path('search/', views.global_search_view, name='global_search'),
    path('suggest/', views.search_suggestions_view, name='search_suggest'),
    
    # Corpus Query Platform (NEW - Pre-analyzed corpus search)
    path('corpus-search/', search_views.corpus_search_view, name='corpus_search'),
    path('collocation/', search_views.collocation_view, name='collocation'),
    path('ngram-analysis/', search_views.ngram_view, name='ngram'),
    path('frequency/', search_views.frequency_view, name='frequency'),
    
    # Corpus search exports
    path('export/concordance/', search_views.export_concordance_view, name='export_concordance'),
    path('export/collocation/', search_views.export_collocation_view, name='export_collocation_results'),
    path('export/ngram/', search_views.export_ngram_view, name='export_ngram'),
    path('export/frequency-list/', search_views.export_frequency_view, name='export_frequency'),
    
    # API endpoints
    path('api/concordance/', search_views.api_concordance, name='api_concordance'),
    
    # Advanced search (Week 9)
    path('advanced-search/', advanced_search_views.advanced_search_view, name='advanced_search'),
    path('query-syntax-help/', advanced_search_views.query_syntax_help, name='query_syntax_help'),
    path('validate-cqp/', advanced_search_views.validate_cqp_query, name='validate_cqp'),
    
    # Main pages
    path('', views.home_view, name='home'),
    path('library/', views.library_view, name='library'),
    path('analysis/<int:doc_id>/', views.analysis_view, name='analysis'),  # Backwards-compat: document-level analysis
    # path('analysis/<int:doc_id>/download/', views.download_search_results, name='download_results'),  # Disabled
    # path('ngrams/<int:doc_id>/', analysis_views.ngrams_view, name='ngrams'),  # Disabled: Use corpus-wide ngram
    # path('wordcloud/<int:doc_id>/', analysis_views.wordcloud_view, name='wordcloud'),  # Disabled
    # path('comparison/', analysis_views.comparison_view, name='comparison'),  # Disabled: Not corpus query feature
    path('statistics/', views.statistics_view, name='statistics'),
    path('corpus-statistics/', statistics_views.corpus_statistics_view, name='corpus_statistics'),
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('my-dashboard/', dashboard_views.user_dashboard_view, name='user_dashboard'),
    path('collections/', collection_views.collections_view, name='collections'),
    path('collections/create/', collection_views.create_collection_view, name='create_collection'),
    path('collections/<int:coll_id>/', collection_views.collection_detail_view, name='collection_detail'),
    path('delete/<int:doc_id>/', views.delete_document, name='delete'),
    # path('export/<int:doc_id>/', views.export_document, name='export'),  # Disabled: Use corpus search exports
    # path('task/<int:task_id>/', views.task_status_view, name='task_status'),  # Disabled: OCR task tracking
    
    # Advanced exports
    path('export/pdf/<int:doc_id>/', export_views.export_pdf_report, name='export_pdf'),
    path('export/excel/<int:doc_id>/', export_views.export_excel_statistics, name='export_excel'),
    path('export/csv/<int:doc_id>/', export_views.export_csv_data, name='export_csv'),
    
    # Watermarked exports (Week 3)
    path('export/concordance/<int:document_id>/', export_views.export_concordance_watermarked, name='export_concordance_watermarked'),
    path('export/frequency/<int:document_id>/', export_views.export_frequency_watermarked, name='export_frequency_watermarked'),
    path('export/conllu/<int:document_id>/', export_views.export_conllu_watermarked, name='export_conllu_watermarked'),
    path('export/history/', export_views.export_history_view, name='export_history'),
    path('download-center/', export_views.download_center_view, name='download_center'),
    
    # Dependency analysis (Week 4 - CoNLL-U)
    path('dependency/<int:document_id>/', dependency_views.dependency_search_view, name='dependency_search'),
    path('dependency/<int:document_id>/tree/<int:sentence_id>/', dependency_views.dependency_tree_page, name='dependency_tree_page'),
    path('dependency/<int:document_id>/tree/<int:sentence_id>/data/', dependency_views.dependency_tree_view, name='dependency_tree_data'),
    path('dependency/<int:document_id>/statistics/', dependency_views.dependency_statistics_view, name='dependency_statistics'),
    
    # Tag management
    path('tags/add/<int:doc_id>/', views.add_tag_to_document, name='add_tag'),
    path('tags/remove/<int:doc_id>/<slug:tag_slug>/', views.remove_tag_from_document, name='remove_tag'),
    path('tags/bulk-add/', views.bulk_add_tags, name='bulk_add_tags'),
    
    # Privacy & Anonymization (Week 6)
    path('privacy/dashboard/', privacy_views.privacy_dashboard_view, name='privacy_dashboard'),
    path('privacy/report/<int:document_id>/', privacy_views.anonymization_report_view, name='anonymization_report'),
    path('privacy/export-data/', privacy_views.export_user_data_view, name='export_user_data'),
    path('privacy/delete-account/', privacy_views.request_account_deletion_view, name='request_deletion'),
    path('privacy-policy/', privacy_views.privacy_policy_view, name='privacy_policy'),
    path('terms/', privacy_views.terms_of_service_view, name='terms_of_service'),
    
    # KVKK/GDPR Compliance (Week 11)
    path('gdpr/settings/', gdpr_views.privacy_settings, name='privacy_settings'),
    
    # Data Export (KVKK/GDPR)
    path('gdpr/data-export/request/', gdpr_views.request_data_export, name='request_data_export'),
    path('gdpr/data-export/list/', gdpr_views.data_export_list, name='data_export_list'),
    path('gdpr/data-export/download/<int:export_id>/', gdpr_views.download_data_export, name='download_data_export'),
    
    # Account Deletion (KVKK/GDPR)
    path('gdpr/account-deletion/request/', gdpr_views.request_account_deletion, name='request_account_deletion'),
    path('gdpr/account-deletion/status/', gdpr_views.account_deletion_status, name='account_deletion_status'),
    path('gdpr/account-deletion/cancel/<int:request_id>/', gdpr_views.cancel_account_deletion, name='cancel_account_deletion'),
    
    # Consent Management (KVKK/GDPR)
    path('gdpr/consent/', gdpr_views.consent_management, name='consent_management'),
    
    # Legal Pages (KVKK/GDPR)
    path('gdpr/privacy-policy/', gdpr_views.privacy_policy, name='gdpr_privacy_policy'),
    path('gdpr/terms/', gdpr_views.terms_of_service, name='gdpr_terms'),
    path('gdpr/kvkk/', gdpr_views.kvkk_notice, name='kvkk_notice'),
]
