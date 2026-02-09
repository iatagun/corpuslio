"""Utility functions for corpus search result exports with watermarks."""

import csv
import json
from io import StringIO
from datetime import datetime
from django.http import HttpResponse


def generate_citation(request_user=None):
    """Generate citation text for corpus data."""
    today = datetime.now().strftime("%d %B %Y")
    citation = (
        f"OCRchestra Korpus Platformu. (2026). Ulusal Türkçe Korpus Veri Tabanı. "
        f"Erişim tarihi: {today}. https://ocrchestra.tr"
    )
    if request_user and request_user.is_authenticated:
        citation += f" | Kullanıcı: {request_user.username}"
    return citation


def export_concordance_csv(results, query, user=None):
    """Export KWIC concordance results to CSV with watermark."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Watermark header
    citation = generate_citation(user)
    writer.writerow(['# OCRchestra Korpus Export'])
    writer.writerow([f'# {citation}'])
    writer.writerow([f'# Arama Sorgusu: {query}'])
    writer.writerow([f'# Toplam Sonuç: {len(results)}'])
    writer.writerow([f'# Export Tarihi: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([])
    
    # Data headers
    writer.writerow(['Sol Bağlam', 'Anahtar Kelime', 'Sağ Bağlam', 'Lemma', 'POS', 'Belge', 'Cümle ID'])
    
    # Data rows
    for result in results:
        writer.writerow([
            result.get('left', ''),
            result.get('keyword', ''),
            result.get('right', ''),
            result.get('lemma', ''),
            result.get('pos', ''),
            result.get('document', ''),
            result.get('sentence_id', '')
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="concordance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    response.write('\ufeff')  # UTF-8 BOM
    
    return response


def export_concordance_json(results, query, user=None):
    """Export KWIC concordance results to JSON with metadata."""
    citation = generate_citation(user)
    
    data = {
        'metadata': {
            'platform': 'OCRchestra Korpus Platformu',
            'citation': citation,
            'query': query,
            'total_results': len(results),
            'export_date': datetime.now().isoformat(),
            'note': 'Bu veri akademik amaçlarla kullanılabilir. Lütfen yukarıdaki atıf bilgisini kullanın.'
        },
        'results': results
    }
    
    response = HttpResponse(json.dumps(data, ensure_ascii=False, indent=2), content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="concordance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response


def export_collocation_csv(collocates, keyword, user=None):
    """Export collocation analysis to CSV."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Watermark
    citation = generate_citation(user)
    writer.writerow(['# OCRchestra Korpus Export - Kollokasyon Analizi'])
    writer.writerow([f'# {citation}'])
    writer.writerow([f'# Anahtar Kelime: {keyword}'])
    writer.writerow([f'# Toplam Kollokat: {len(collocates)}'])
    writer.writerow([f'# Export Tarihi: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([])
    
    # Headers
    writer.writerow(['Sıra', 'Kollokat', 'Frekans', 'Sol Pozisyon', 'Sağ Pozisyon'])
    
    # Data
    for idx, coll in enumerate(collocates, 1):
        writer.writerow([
            idx,
            coll.get('word', ''),
            coll.get('frequency', 0),
            coll.get('left_count', 0),
            coll.get('right_count', 0)
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="collocation_{keyword}_{datetime.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')
    
    return response


def export_ngram_csv(ngrams, n, user=None):
    """Export n-gram analysis to CSV."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Watermark
    citation = generate_citation(user)
    writer.writerow([f'# OCRchestra Korpus Export - {n}-gram Analizi'])
    writer.writerow([f'# {citation}'])
    writer.writerow([f'# Toplam {n}-gram: {len(ngrams)}'])
    writer.writerow([f'# Export Tarihi: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([])
    
    # Headers
    writer.writerow(['Sıra', 'N-gram', 'Frekans'])
    
    # Data
    for idx, ngram in enumerate(ngrams, 1):
        writer.writerow([
            idx,
            ngram.get('ngram', ''),
            ngram.get('frequency', 0)
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{n}gram_{datetime.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')
    
    return response


def export_frequency_csv(frequencies, user=None):
    """Export word frequency list to CSV."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Watermark
    citation = generate_citation(user)
    writer.writerow(['# OCRchestra Korpus Export - Frekans Listesi'])
    writer.writerow([f'# {citation}'])
    writer.writerow([f'# Toplam Token: {len(frequencies)}'])
    writer.writerow([f'# Export Tarihi: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([])
    
    # Headers
    writer.writerow(['Sıra', 'Kelime/Lemma', 'Frekans'])
    
    # Data
    for idx, freq in enumerate(frequencies, 1):
        writer.writerow([
            idx,
            freq.get('word', ''),
            freq.get('frequency', 0)
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="frequency_{datetime.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')
    
    return response
