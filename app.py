"""OCRchestra Streamlit UI.

Provides a graphical interface for:
- Managing the document library (database)
- Uploading and processing new documents
- Viewing corpus analysis (concordance, stats)
"""
import streamlit as st
import tempfile
import os
import time
from pathlib import Path
import json

from ocrchestra.database import DatabaseManager
from ocrchestra import OllamaOrchestrator

# Initialize Database
db = DatabaseManager()

st.set_page_config(
    page_title="OCRchestra - Corpus Manager",
    page_icon="📚",
    layout="wide"
)

def get_orchestrator():
    """Singleton orchestrator."""
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = OllamaOrchestrator()
    return st.session_state.orchestrator

def main():
    st.title("📚 OCRchestra - Corpus Manager")

    # Tabs
    tab_library, tab_process, tab_corpus = st.tabs(["Kütüphane", "Yeni Ekle", "Derlem İncele"])

    # --- TAB 1: LIBRARY ---
    with tab_library:
        st.header("Mevcut Kitaplar")
        docs = db.get_all_documents()
        
        if not docs:
            st.info("Kütüphane boş. 'Yeni Ekle' sekmesinden kitap ekleyebilirsiniz.")
        else:
            for doc in docs:
                with st.expander(f"{doc['filename']} ({doc['format']}) - {doc['upload_date']}"):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"Durum: {'✅ İşlendi' if doc['processed'] else '⏳ Bekliyor'}")
                    with col2:
                        if st.button("Sil", key=f"del_{doc['id']}"):
                            db.delete_document(doc['id'])
                            st.rerun()

    # --- TAB 2: PROCESS ---
    with tab_process:
        st.header("Yeni Belge İşle")
        
        uploaded_file = st.file_uploader("Bir dosya seçin", type=['pdf', 'docx', 'txt', 'png', 'jpg'])
        
        if uploaded_file:
            st.write(f"Seçilen dosya: {uploaded_file.name}")
            
            # Options
            analyze_option = st.checkbox("Dilbilimsel Analiz Yap (POS/Lemma)", value=True)
            label_studio_option = st.checkbox("Label Studio Formatında Kaydet", value=False)
            
            if st.button("İşlemi Başlat"):
                with st.spinner("İşleniyor... Bu işlem dosya boyutuna ve modele göre zaman alabilir."):
                    # Save to temp file
                    suffix = Path(uploaded_file.name).suffix
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    
                    try:
                        # 1. Add to DB (Pending)
                        doc_entry = db.add_document(uploaded_file.name, suffix)
                        
                        # 2. Process
                        orch = get_orchestrator()
                        
                        # Use process_and_export logic manually to capture data for DB
                        step_status = st.empty()
                        
                        step_status.info("Metin çıkarılıyor...")
                        res = orch.process(tmp_path)
                        
                        if res['success']:
                            text = res.get('text', '')
                            
                            step_status.info("Metin temizleniyor...")
                            cleaned_text = orch.corpus_expert.clean_text(text)
                            
                            analysis = []
                            if analyze_option:
                                step_status.info("Analiz yapılıyor (Ollama)...")
                                analysis = orch.corpus_expert.analyze_with_ollama(cleaned_text)
                            
                            # Save results to DB
                            db.save_results(doc_entry.id, text, cleaned_text, analysis)
                            
                            step_status.success("İşlem tamamlandı! Veritabanına kaydedildi.")
                            
                            # Optional: Label Studio Export
                            if label_studio_option:
                                export_path = f"exports/{uploaded_file.name}.json"
                                orch.corpus_expert.export_to_label_studio(cleaned_text, analysis, export_path)
                                st.success(f"Label Studio dosyası oluşturuldu: {export_path}")
                                
                        else:
                            st.error(f"Hata: {res.get('error')}")
                            
                    finally:
                        os.unlink(tmp_path)

    # --- TAB 3: CORPUS VIEWER ---
    with tab_corpus:
        st.header("Derlem İncele")
        
        # Select Document
        docs = db.get_all_documents()
        processed_docs = [d for d in docs if d['processed']]
        
        if not processed_docs:
            st.warning("Henüz işlenmiş belge yok.")
        else:
            selected_doc_name = st.selectbox(
                "Belge Seçin", 
                [f"{d['id']}: {d['filename']}" for d in processed_docs]
            )
            
            if selected_doc_name:
                doc_id = int(selected_doc_name.split(":")[0])
                doc = db.get_document(doc_id)
                
                if doc:
                    # Dashboard
                    c1, c2, c3 = st.columns(3)
                    words = doc['cleaned_text'].split()
                    c1.metric("Kelime Sayısı", len(words))
                    c2.metric("Karakter Sayısı", len(doc['cleaned_text']))
                    c3.metric("Format", doc['format'])
                    
                    st.divider()
                    
                    # Concordance Search
                    st.subheader("Beriçim (Concordance / KWIC)")
                    keyword = st.text_input("Anahtar Kelime Ara")
                    
                    if keyword:
                        # Simple Regex/Slice based KWIC
                        import re
                        lines = []
                        window = 50
                        matches = [m.start() for m in re.finditer(re.escape(keyword), doc['cleaned_text'], re.IGNORECASE)]
                        
                        if matches:
                            st.write(f"{len(matches)} eşleşme bulundu.")
                            data = []
                            for m in matches:
                                start = max(0, m - window)
                                end = min(len(doc['cleaned_text']), m + len(keyword) + window)
                                left = doc['cleaned_text'][start:m]
                                center = doc['cleaned_text'][m:m+len(keyword)]
                                right = doc['cleaned_text'][m+len(keyword):end]
                                data.append({"Sol": left, "Anahtar": center, "Sağ": right})
                            
                            st.table(data)
                        else:
                            st.info("Eşleşme bulunamadı.")
                    
                    st.divider()
                    
                    # Analysis Viewer
                    st.subheader("📋 Dilbilimsel Analiz Detayları")
                    
                    if doc.get('analysis'):
                        analysis_data = doc['analysis']
                        import pandas as pd
                        df = pd.DataFrame(analysis_data)
                        
                        # --- 1. Statistics Cards ---
                        st.markdown("##### 📊 İstatistikler")
                        
                        # Calculate counts
                        total_words = len(df)
                        review_count = 0
                        low_conf_count = 0
                        avg_confidence = 0.0
                        
                        if 'needs_review' in df.columns:
                            review_count = df['needs_review'].sum()
                        if 'confidence' in df.columns:
                            low_conf_count = (df['confidence'] < 0.6).sum()
                            avg_confidence = df['confidence'].mean()
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Toplam Kelime", total_words)
                        c2.metric("⚠️ İnceleme Gerekli", review_count)
                        c3.metric("Düşük Güven (<0.6)", low_conf_count)
                        c4.metric("Ort. Güven", f"{avg_confidence:.2f}" if avg_confidence > 0 else "N/A")
                        
                        # Show POS distribution if available
                        if 'pos' in df.columns:
                            pos_counts = df['pos'].value_counts()
                            st.caption(f"📌 En Çok: {pos_counts.index[0]} ({pos_counts.values[0]})")
                        
                        st.divider()

                        # --- 2. Review Queue Filter ---
                        st.markdown("##### 🔍 Filtreler ve Arama")
                        
                        col_filter1, col_filter2, col_filter3 = st.columns(3)
                        
                        # Safe access to unique values
                        pos_options = []
                        if 'pos' in df.columns:
                            pos_options = df['pos'].dropna().unique()

                        with col_filter1:
                            review_only = st.checkbox("🚨 Sadece İnceleme Gerekenleri Göster", value=False)
                        
                        with col_filter2:
                            selected_pos = st.multiselect(
                                "POS Filtresi", 
                                options=pos_options,
                                default=[]
                            )
                        
                        with col_filter3:
                            search_lemma = st.text_input("Lemma Ara (Örn: gel, git)")
                        
                        # Apply filters
                        filtered_df = df.copy()
                        
                        if review_only and 'needs_review' in df.columns:
                            filtered_df = filtered_df[filtered_df['needs_review'] == True]
                        
                        if selected_pos and 'pos' in df.columns:
                            filtered_df = filtered_df[filtered_df['pos'].isin(selected_pos)]
                        
                        if search_lemma and 'lemma' in df.columns:
                            filtered_df = filtered_df[filtered_df['lemma'].str.contains(search_lemma, case=False, na=False)]
                        
                        # Sort by confidence (ascending) to show problematic first
                        if 'confidence' in filtered_df.columns:
                            filtered_df = filtered_df.sort_values('confidence')
                        
                        st.dataframe(
                            filtered_df, 
                            use_container_width=True,
                            column_config={
                                "word": "Kelime",
                                "lemma": "Kök (Lemma)",
                                "pos": "Tür (POS)",
                                "confidence": st.column_config.ProgressColumn(
                                    "Güven",
                                    help="Etiketin doğruluk güveni",
                                    format="%.2f",
                                    min_value=0,
                                    max_value=1,
                                ),
                                "warning": "⚠️ Uyarı",
                                "needs_review": st.column_config.CheckboxColumn("İnceleme?")
                            }
                        )
                        
                        st.divider()

                        # --- 3. Visual Text View (Annotated) ---
                        st.markdown("##### 🎨 Görsel Metin Analizi")
                        st.info("Metin üzerinde kelime türleri renkli olarak gösterilmektedir. ⚠️ işareti düşük güvenli etiketleri gösterir.")

                        # Color Mapping
                        pos_colors = {
                            "NOUN": "#8ea1e6",
                            "VERB": "#e68e8e",
                            "ADJ": "#8ee6a7",
                            "ADV": "#e6d38e",
                            "PRON": "#d58ee6",
                            "DET": "#cccccc",
                            "ADP": "#cccccc",
                            "NUM": "#8ee6e6",
                            "PUNCT": "#ffffff"
                        }

                        html_output = '<div style="line-height: 2.5; background-color: #262730; padding: 20px; border-radius: 10px;">'
                        
                        vis_limit = 500
                        
                        for item in analysis_data[:vis_limit]:
                            if isinstance(item, dict):
                                word = item.get('word', '')
                                pos = item.get('pos', 'UNK')
                                lemma = item.get('lemma', '')
                                confidence = item.get('confidence', 1.0)
                                needs_review = item.get('needs_review', False)
                                warning = item.get('warning', '')
                            else:
                                word = str(item)
                                pos = 'UNK'
                                lemma = ''
                                confidence = 1.0
                                needs_review = False
                                warning = ''

                            color = pos_colors.get(pos, "#bbbbbb")
                            
                            # Build tooltip with confidence info
                            tooltip = f"Lemma: {lemma} | POS: {pos} | Güven: {confidence:.2f}"
                            if warning:
                                tooltip += f" | ⚠️ {warning}"
                            
                            # Add warning indicator for low confidence
                            display_word = word
                            if needs_review or confidence < 0.6:
                                display_word = f"⚠️{word}"
                            
                            html_output += (
                                f'<span style="background-color: {color}40; '
                                f'color: #ffffff; '
                                f'padding: 2px 6px; '
                                f'margin: 0 2px; '
                                f'border-radius: 4px; '
                                f'border-bottom: 2px solid {color};" '
                                f'title="{tooltip}">{display_word}</span> '
                            )
                        
                        if len(analysis_data) > vis_limit:
                            html_output += f'<br><br><i>... (Geri kalan {len(analysis_data) - vis_limit} kelime gizlendi) ...</i>'
                        
                        html_output += '</div>'
                        
                        st.markdown(html_output, unsafe_allow_html=True)
                        
                        st.caption("🔵 İsim | 🔴 Fiil | 🟢 Sıfat | 🟡 Zarf | 🟣 Zamir | ⚠️ İnceleme Gerekli")

                    else:
                        st.info("Bu belge için POS/Lemma analizi yapılmamış.")

                    with st.expander("Ham Metni Göster"):
                        st.text_area("Metin", doc['cleaned_text'], height=300)

if __name__ == "__main__":
    main()
