"""Advanced export views for various formats (PDF, Excel, CSV)."""

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Document
from collections import Counter
import csv
import io


@login_required
def export_pdf_report(request, doc_id):
    """Export document analysis as a PDF report."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from datetime import datetime
    
    document = get_object_or_404(Document, id=doc_id, processed=True)
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="analiz_raporu_{document.id}.pdf"'
    
    # Create PDF
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Container for elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#334155'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    elements.append(Paragraph("Korpus Analiz Raporu", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Document info
    info_data = [
        ['Belge Adı:', document.title],
        ['Format:', document.format],
        ['Yükleme Tarihi:', document.upload_date.strftime('%d.%m.%Y %H:%M')],
        ['Rapor Tarihi:', datetime.now().strftime('%d.%m.%Y %H:%M')],
    ]
    
    if document.author:
        info_data.insert(1, ['Yazar:', document.author])
    
    info_table = Table(info_data, colWidths=[5*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 1*cm))
    
    # Get analysis data
    data = document.analysis.data if hasattr(document, 'analysis') else []
    
    # Statistics
    elements.append(Paragraph("İstatistikler", heading_style))
    
    words = [item.get('word', '').lower() for item in data if isinstance(item, dict)]
    lemmas = [item.get('lemma', '').lower() for item in data if isinstance(item, dict) and item.get('lemma')]
    pos_tags = [item.get('pos', '') for item in data if isinstance(item, dict) and item.get('pos')]
    
    stats_data = [
        ['Metrik', 'Değer'],
        ['Toplam Kelime', f'{len(words):,}'.replace(',', '.')],
        ['Benzersiz Kelime', f'{len(set(words)):,}'.replace(',', '.')],
        ['Benzersiz Kök', f'{len(set(lemmas)):,}'.replace(',', '.')],
        ['POS Etiket', f'{len(pos_tags):,}'.replace(',', '.')],
        ['Ortalama Kelime Uzunluğu', f'{sum(len(w) for w in words) / len(words):.2f}' if words else '0'],
    ]
    
    stats_table = Table(stats_data, colWidths=[10*cm, 7*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 1*cm))
    
    # Top words
    elements.append(Paragraph("En Sık Kullanılan Kelimeler (Top 20)", heading_style))
    word_freq = Counter(words).most_common(20)
    
    word_data = [['Sıra', 'Kelime', 'Frekans']]
    for i, (word, freq) in enumerate(word_freq, 1):
        word_data.append([str(i), word, f'{freq:,}'.replace(',', '.')])
    
    word_table = Table(word_data, colWidths=[2*cm, 10*cm, 5*cm])
    word_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(word_table)
    elements.append(PageBreak())
    
    # POS distribution
    elements.append(Paragraph("POS Etiket Dağılımı (Top 15)", heading_style))
    pos_freq = Counter(pos_tags).most_common(15)
    
    pos_data = [['Sıra', 'POS Etiketi', 'Frekans', 'Yüzde']]
    total_pos = len(pos_tags)
    for i, (pos, freq) in enumerate(pos_freq, 1):
        percentage = (freq / total_pos * 100) if total_pos > 0 else 0
        pos_data.append([str(i), pos, f'{freq:,}'.replace(',', '.'), f'{percentage:.1f}%'])
    
    pos_table = Table(pos_data, colWidths=[2*cm, 6*cm, 5*cm, 4*cm])
    pos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#a855f7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(pos_table)
    
    # Build PDF
    pdf.build(elements)
    
    # Get value and write to response
    pdf_value = buffer.getvalue()
    buffer.close()
    response.write(pdf_value)
    
    return response


@login_required
def export_excel_statistics(request, doc_id):
    """Export document statistics to Excel."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    document = get_object_or_404(Document, id=doc_id, processed=True)
    
    # Create workbook
    wb = Workbook()
    
    # Get analysis data
    data = document.analysis.data if hasattr(document, 'analysis') else []
    words = [item.get('word', '').lower() for item in data if isinstance(item, dict)]
    lemmas = [item.get('lemma', '').lower() for item in data if isinstance(item, dict) and item.get('lemma')]
    pos_tags = [item.get('pos', '') for item in data if isinstance(item, dict) and item.get('pos')]
    
    # Sheet 1: Overview
    ws1 = wb.active
    ws1.title = "Genel Bakış"
    
    # Header styling
    header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    
    # Document info
    ws1['A1'] = "Belge Bilgileri"
    ws1['A1'].font = Font(bold=True, size=14)
    ws1.merge_cells('A1:B1')
    
    info_rows = [
        ['Belge Adı', document.title],
        ['Format', document.format],
        ['Yükleme Tarihi', document.upload_date.strftime('%d.%m.%Y %H:%M')],
        ['Yazar', document.author or 'Bilinmiyor'],
    ]
    
    row = 3
    for label, value in info_rows:
        ws1[f'A{row}'] = label
        ws1[f'B{row}'] = value
        ws1[f'A{row}'].font = Font(bold=True)
        ws1[f'A{row}'].fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        row += 1
    
    # Statistics
    ws1[f'A{row+1}'] = "İstatistikler"
    ws1[f'A{row+1}'].font = Font(bold=True, size=14)
    ws1.merge_cells(f'A{row+1}:B{row+1}')
    
    stats_rows = [
        ['Toplam Kelime', len(words)],
        ['Benzersiz Kelime', len(set(words))],
        ['Benzersiz Kök', len(set(lemmas))],
        ['POS Etiket', len(pos_tags)],
        ['Ortalama Kelime Uzunluğu', round(sum(len(w) for w in words) / len(words), 2) if words else 0],
    ]
    
    row += 3
    for label, value in stats_rows:
        ws1[f'A{row}'] = label
        ws1[f'B{row}'] = value
        ws1[f'A{row}'].font = Font(bold=True)
        ws1[f'A{row}'].fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        ws1[f'B{row}'].number_format = '#,##0'
        row += 1
    
    # Adjust column widths
    ws1.column_dimensions['A'].width = 25
    ws1.column_dimensions['B'].width = 30
    
    # Sheet 2: Word Frequencies
    ws2 = wb.create_sheet("Kelime Frekansları")
    ws2['A1'] = "Sıra"
    ws2['B1'] = "Kelime"
    ws2['C1'] = "Frekans"
    
    for cell in ['A1', 'B1', 'C1']:
        ws2[cell].fill = header_fill
        ws2[cell].font = header_font
        ws2[cell].alignment = Alignment(horizontal='center', vertical='center')
        ws2[cell].border = border
    
    word_freq = Counter(words).most_common(100)
    for i, (word, freq) in enumerate(word_freq, 2):
        ws2[f'A{i}'] = i - 1
        ws2[f'B{i}'] = word
        ws2[f'C{i}'] = freq
        ws2[f'C{i}'].number_format = '#,##0'
        
        for cell in [f'A{i}', f'B{i}', f'C{i}']:
            ws2[cell].border = border
    
    ws2.column_dimensions['A'].width = 8
    ws2.column_dimensions['B'].width = 30
    ws2.column_dimensions['C'].width = 15
    
    # Sheet 3: Lemma Frequencies
    ws3 = wb.create_sheet("Kök Frekansları")
    ws3['A1'] = "Sıra"
    ws3['B1'] = "Kök"
    ws3['C1'] = "Frekans"
    
    for cell in ['A1', 'B1', 'C1']:
        ws3[cell].fill = header_fill
        ws3[cell].font = header_font
        ws3[cell].alignment = Alignment(horizontal='center', vertical='center')
        ws3[cell].border = border
    
    lemma_freq = Counter(lemmas).most_common(100)
    for i, (lemma, freq) in enumerate(lemma_freq, 2):
        ws3[f'A{i}'] = i - 1
        ws3[f'B{i}'] = lemma
        ws3[f'C{i}'] = freq
        ws3[f'C{i}'].number_format = '#,##0'
        
        for cell in [f'A{i}', f'B{i}', f'C{i}']:
            ws3[cell].border = border
    
    ws3.column_dimensions['A'].width = 8
    ws3.column_dimensions['B'].width = 30
    ws3.column_dimensions['C'].width = 15
    
    # Sheet 4: POS Distribution
    ws4 = wb.create_sheet("POS Dağılımı")
    ws4['A1'] = "Sıra"
    ws4['B1'] = "POS Etiketi"
    ws4['C1'] = "Frekans"
    ws4['D1'] = "Yüzde"
    
    for cell in ['A1', 'B1', 'C1', 'D1']:
        ws4[cell].fill = header_fill
        ws4[cell].font = header_font
        ws4[cell].alignment = Alignment(horizontal='center', vertical='center')
        ws4[cell].border = border
    
    pos_freq = Counter(pos_tags).most_common(50)
    total_pos = len(pos_tags)
    for i, (pos, freq) in enumerate(pos_freq, 2):
        percentage = (freq / total_pos * 100) if total_pos > 0 else 0
        ws4[f'A{i}'] = i - 1
        ws4[f'B{i}'] = pos
        ws4[f'C{i}'] = freq
        ws4[f'D{i}'] = percentage
        ws4[f'C{i}'].number_format = '#,##0'
        ws4[f'D{i}'].number_format = '0.00"%"'
        
        for cell in [f'A{i}', f'B{i}', f'C{i}', f'D{i}']:
            ws4[cell].border = border
    
    ws4.column_dimensions['A'].width = 8
    ws4.column_dimensions['B'].width = 20
    ws4.column_dimensions['C'].width = 15
    ws4.column_dimensions['D'].width = 12
    
    # Save to response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="istatistikler_{document.id}.xlsx"'
    wb.save(response)
    
    return response


@login_required
def export_csv_data(request, doc_id):
    """Export raw analysis data to CSV."""
    document = get_object_or_404(Document, id=doc_id, processed=True)
    
    # Get format type
    format_type = request.GET.get('type', 'words')  # words, lemmas, pos, full
    
    # Create response
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="veri_{format_type}_{document.id}.csv"'
    
    writer = csv.writer(response)
    
    # Get analysis data
    data = document.analysis.data if hasattr(document, 'analysis') else []
    
    if format_type == 'words':
        # Word frequency CSV
        words = [item.get('word', '').lower() for item in data if isinstance(item, dict)]
        word_freq = Counter(words).most_common()
        
        writer.writerow(['Kelime', 'Frekans'])
        for word, freq in word_freq:
            writer.writerow([word, freq])
            
    elif format_type == 'lemmas':
        # Lemma frequency CSV
        lemmas = [item.get('lemma', '').lower() for item in data if isinstance(item, dict) and item.get('lemma')]
        lemma_freq = Counter(lemmas).most_common()
        
        writer.writerow(['Kök', 'Frekans'])
        for lemma, freq in lemma_freq:
            writer.writerow([lemma, freq])
            
    elif format_type == 'pos':
        # POS distribution CSV
        pos_tags = [item.get('pos', '') for item in data if isinstance(item, dict) and item.get('pos')]
        pos_freq = Counter(pos_tags).most_common()
        total = len(pos_tags)
        
        writer.writerow(['POS Etiketi', 'Frekans', 'Yüzde'])
        for pos, freq in pos_freq:
            percentage = (freq / total * 100) if total > 0 else 0
            writer.writerow([pos, freq, f'{percentage:.2f}'])
            
    else:  # full
        # Full analysis data
        writer.writerow(['Sıra', 'Kelime', 'Kök', 'POS', 'Cümle ID'])
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                writer.writerow([
                    i,
                    item.get('word', ''),
                    item.get('lemma', ''),
                    item.get('pos', ''),
                    item.get('sentence_id', '')
                ])
    
    return response
