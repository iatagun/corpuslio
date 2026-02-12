"""Utility functions for corpus search result exports with watermarks.

These helpers now also record `ExportLog` entries and update `UserProfile`
quotas when a `user` is provided so exports initiated from the search UI
are tracked the same way as the dedicated export views.
"""

import csv
import json
from io import StringIO
from datetime import datetime
from decimal import Decimal
from django.http import HttpResponse
from django.utils import timezone

# Import models for logging/quotas
from .models import ExportLog, UserProfile
from .permissions import has_role


def generate_citation(request_user=None):
    """Generate citation text for corpus data."""
    today = datetime.now().strftime("%d %B %Y")
    citation = (
        f"CorpusLIO Korpus Platformu. (2026). Ulusal Türkçe Korpus Veri Tabanı. "
        f"Erişim tarihi: {today}. https://corpuslio.com"
    )
    if request_user and request_user.is_authenticated:
        citation += f" | Kullanıcı: {request_user.username}"
    return citation


def export_concordance_csv(results, query, user=None):
    """Export KWIC concordance results to CSV with watermark.
    
    For verified researchers: includes full linguistic annotations (morphology, dependency).
    For regular users: basic lemma and POS.
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Check if user is verified researcher
    is_verified = user and has_role(user, 'verified')
    
    # Watermark header
    citation = generate_citation(user)
    writer.writerow(['# CorpusLIO Korpus Export'])
    writer.writerow([f'# {citation}'])
    writer.writerow([f'# Arama Sorgusu: {query}'])
    writer.writerow([f'# Toplam Sonuç: {len(results)}'])
    writer.writerow([f'# Export Tarihi: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    if is_verified:
        writer.writerow(['# Format: Tam Dilbilimsel Açıklamalar (Doğrulanmış Araştırmacı)'])
    writer.writerow([])
    
    # Data headers - extended for verified researchers
    if is_verified:
        writer.writerow([
            'Sol Bağlam', 'Anahtar Kelime', 'Sağ Bağlam', 
            'Lemma', 'UPOS', 'XPOS',
            'Morfolojik Özellikler', 'Dependency İlişkisi', 'Head ID',
            'Belge', 'Cümle ID'
        ])
    else:
        writer.writerow(['Sol Bağlam', 'Anahtar Kelime', 'Sağ Bağlam', 'Lemma', 'POS', 'Belge', 'Cümle ID'])
    
    # Data rows
    for result in results:
        if is_verified:
            writer.writerow([
                result.get('left', ''),
                result.get('keyword', ''),
                result.get('right', ''),
                result.get('lemma', ''),
                result.get('upos', result.get('pos', '')),
                result.get('xpos', ''),
                result.get('feats', ''),
                result.get('deprel', ''),
                result.get('head', ''),
                result.get('document', ''),
                result.get('sentence_id', '')
            ])
        else:
            writer.writerow([
                result.get('left', ''),
                result.get('keyword', ''),
                result.get('right', ''),
                result.get('lemma', ''),
                result.get('pos', ''),
                result.get('document', ''),
                result.get('sentence_id', '')
            ])
    
    # Finalize bytes (include UTF-8 BOM) and log export
    content_str = output.getvalue()
    content_bytes = ('\ufeff' + content_str).encode('utf-8')
    filename = f'concordance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return _finalize_export(content_bytes, filename, 'concordance', 'csv', user, query, len(results))


def export_concordance_json(results, query, user=None):
    """Export KWIC concordance results to JSON with metadata.
    
    For verified researchers: includes annotation_level field and full linguistic data.
    """
    citation = generate_citation(user)
    is_verified = user and has_role(user, 'verified')
    
    data = {
        'metadata': {
            'platform': 'CorpusLIO Korpus Platformu',
            'citation': citation,
            'query': query,
            'total_results': len(results),
            'export_date': datetime.now().isoformat(),
            'annotation_level': 'full_linguistic' if is_verified else 'basic',
            'user_role': 'verified_researcher' if is_verified else 'registered',
            'note': 'Bu veri akademik amaçlarla kullanılabilir. Lütfen yukarıdaki atıf bilgisini kullanın.',
            'schema': {
                'upos': 'Universal POS tag (CoNLL-U)',
                'xpos': 'Language-specific POS tag',
                'feats': 'Morphological features (Case, Number, Person, etc.)',
                'deprel': 'Dependency relation',
                'head': 'Head token ID in dependency tree'
            } if is_verified else None
        },
        'results': results
    }
    
    content_str = json.dumps(data, ensure_ascii=False, indent=2)
    content_bytes = content_str.encode('utf-8')
    filename = f'concordance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return _finalize_export(content_bytes, filename, 'concordance', 'json', user, query, len(results))


def export_collocation_csv(collocates, keyword, user=None):
    """Export collocation analysis to CSV.
    
    For verified researchers: includes POS tags and lemma forms.
    """
    output = StringIO()
    writer = csv.writer(output)
    
    is_verified = user and has_role(user, 'verified')
    
    # Watermark
    citation = generate_citation(user)
    writer.writerow(['# CorpusLIO Korpus Export - Kollokasyon Analizi'])
    writer.writerow([f'# {citation}'])
    writer.writerow([f'# Anahtar Kelime: {keyword}'])
    writer.writerow([f'# Toplam Kollokat: {len(collocates)}'])
    writer.writerow([f'# Export Tarihi: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    if is_verified:
        writer.writerow(['# Format: Lemma ve POS Bilgili (Doğrulanmış Araştırmacı)'])
    writer.writerow([])
    
    # Headers
    if is_verified:
        writer.writerow(['Sıra', 'Kollokat', 'Lemma', 'POS', 'Frekans', 'Sol Pozisyon', 'Sağ Pozisyon', 'MI Skoru'])
    else:
        writer.writerow(['Sıra', 'Kollokat', 'Frekans', 'Sol Pozisyon', 'Sağ Pozisyon'])
    
    # Data
    for idx, coll in enumerate(collocates, 1):
        if is_verified:
            writer.writerow([
                idx,
                coll.get('word', ''),
                coll.get('lemma', ''),
                coll.get('pos', ''),
                coll.get('frequency', 0),
                coll.get('left_count', 0),
                coll.get('right_count', 0),
                coll.get('mi_score', '')
            ])
        else:
            writer.writerow([
                idx,
                coll.get('word', ''),
                coll.get('frequency', 0),
                coll.get('left_count', 0),
                coll.get('right_count', 0)
            ])
    
    content_str = output.getvalue()
    content_bytes = ('\ufeff' + content_str).encode('utf-8')
    filename = f'collocation_{keyword}_{datetime.now().strftime("%Y%m%d")}.csv'
    return _finalize_export(content_bytes, filename, 'statistics', 'csv', user, keyword, len(collocates))


def export_ngram_csv(ngrams, n, user=None):
    """Export n-gram analysis to CSV.
    
    For verified researchers: includes lemma and POS tag breakdown for each n-gram.
    """
    output = StringIO()
    writer = csv.writer(output)
    
    is_verified = user and has_role(user, 'verified')
    
    # Watermark
    citation = generate_citation(user)
    writer.writerow([f'# CorpusLIO Korpus Export - {n}-gram Analizi'])
    writer.writerow([f'# {citation}'])
    writer.writerow([f'# Toplam {n}-gram: {len(ngrams)}'])
    writer.writerow([f'# Export Tarihi: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    if is_verified:
        writer.writerow(['# Format: Lemma ve POS Bilgili (Doğrulanmış Araştırmacı)'])
    writer.writerow([])
    
    # Headers
    if is_verified:
        writer.writerow(['Sıra', 'N-gram', 'Frekans', 'Lemma Dizisi', 'POS Dizisi'])
    else:
        writer.writerow(['Sıra', 'N-gram', 'Frekans'])
    
    # Data
    for idx, ngram in enumerate(ngrams, 1):
        if is_verified:
            writer.writerow([
                idx,
                ngram.get('ngram', ''),
                ngram.get('frequency', 0),
                ngram.get('lemma_sequence', ''),
                ngram.get('pos_sequence', '')
            ])
        else:
            writer.writerow([
                idx,
                ngram.get('ngram', ''),
                ngram.get('frequency', 0)
            ])
    
    content_str = output.getvalue()
    content_bytes = ('\ufeff' + content_str).encode('utf-8')
    filename = f'{n}gram_{datetime.now().strftime("%Y%m%d")}.csv'
    return _finalize_export(content_bytes, filename, 'statistics', 'csv', user, f'{n}-gram', len(ngrams))


def export_frequency_csv(frequencies, user=None):
    """Export word frequency list to CSV.
    
    For verified researchers: includes POS tag distribution.
    """
    output = StringIO()
    writer = csv.writer(output)
    
    is_verified = user and has_role(user, 'verified')
    
    # Watermark
    citation = generate_citation(user)
    writer.writerow(['# CorpusLIO Korpus Export - Frekans Listesi'])
    writer.writerow([f'# {citation}'])
    writer.writerow([f'# Toplam Token: {len(frequencies)}'])
    writer.writerow([f'# Export Tarihi: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    if is_verified:
        writer.writerow(['# Format: POS Etiketli (Doğrulanmış Araştırmacı)'])
    writer.writerow([])
    
    # Headers
    if is_verified:
        writer.writerow(['Sıra', 'Kelime/Lemma', 'Frekans', 'POS Etiketi'])
    else:
        writer.writerow(['Sıra', 'Kelime/Lemma', 'Frekans'])
    
    # Data
    for idx, freq in enumerate(frequencies, 1):
        if is_verified:
            writer.writerow([
                idx,
                freq.get('word', ''),
                freq.get('frequency', 0),
                freq.get('pos', '')
            ])
        else:
            writer.writerow([
                idx,
                freq.get('word', ''),
                freq.get('frequency', 0)
            ])
    
    content_str = output.getvalue()
    content_bytes = ('\ufeff' + content_str).encode('utf-8')
    filename = f'frequency_{datetime.now().strftime("%Y%m%d")}.csv'
    return _finalize_export(content_bytes, filename, 'frequency', 'csv', user, '', len(frequencies))


def _finalize_export(content_bytes, filename, export_type, fmt, user, query_text, row_count, document=None):
    """Create HttpResponse for export bytes and record ExportLog + update quota.

    - `content_bytes` should already include any BOM and be encoded.
    - `user` may be None for anonymous exports; logging requires an authenticated user.
    """
    response = HttpResponse(content_bytes, content_type=('application/octet-stream' if fmt not in ('csv','json') else f'text/{fmt}; charset=utf-8'))
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    file_size_bytes = len(content_bytes)
    file_size_mb = Decimal(file_size_bytes) / Decimal(1024 * 1024) if file_size_bytes > 0 else Decimal('0.00')

    # If user provided, update quota and create ExportLog
    if user and getattr(user, 'is_authenticated', False):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.reset_export_quota_if_needed()
        quota_before = profile.export_used_mb

        if not user.is_superuser:
            profile.use_export_quota(file_size_mb)

        quota_after = profile.export_used_mb

        # Check user watermark preference
        watermark_enabled = profile.enable_watermark if profile else True

        # Create ExportLog
        ExportLog.objects.create(
            user=user,
            ip_address=None,
            export_type=export_type,
            format=fmt,
            document=document,
            query_text=query_text or '',
            row_count=row_count or 0,
            file_size_bytes=file_size_bytes,
            watermark_applied=watermark_enabled,  # Respect user preference
            citation_text=generate_citation(user) if watermark_enabled else '',
            quota_before_mb=quota_before,
            quota_after_mb=quota_after,
            document_title=filename,  # Save the generated filename
        )

    return response
