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

def get_llm_client():
    """Get configured LLM client (Groq only)."""
    if 'llm_client' not in st.session_state:
        # Check for Groq API key
        if hasattr(st, 'secrets') and 'GROQ_API_KEY' in st.secrets:
            from ocrchestra.groq_client import GroqClient
            st.session_state.llm_client = GroqClient(
                api_key=st.secrets['GROQ_API_KEY']
            )
            st.session_state.provider = 'Groq'
        else:
            st.session_state.llm_client = None
            st.session_state.provider = None
    
    return st.session_state.llm_client

def get_orchestrator():
    """Singleton orchestrator."""
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = OllamaOrchestrator()
        # Update with current client
        client = get_llm_client()
        if client:
            st.session_state.orchestrator.ollama_client = client
    return st.session_state.orchestrator

# Custom CSS for Academic Minimalist Design
def load_custom_css():
    st.markdown("""
    <style>
    /* Base Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main Title */
    h1 {
        font-size: 28px !important;
        font-weight: 600 !important;
        color: #1e3a8a !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem !important;
    }
    
    /* Section Headers */
    h2 {
        font-size: 20px !important;
        font-weight: 500 !important;
        color: #334155 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        font-size: 16px !important;
        font-weight: 500 !important;
        color: #475569 !important;
        margin-top: 1.5rem !important;
    }
    
    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }
    
    /* Clean metric cards */
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-family: 'JetBrains Mono', monospace !important;
        color: #1e3a8a !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: #64748b !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] .element-container {
        font-size: 14px;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #3b82f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        background-color: #2563eb !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {
        border-color: #cbd5e1 !important;
        border-radius: 6px !important;
        font-size: 14px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-weight: 500 !important;
        font-size: 15px !important;
        color: #64748b !important;
        padding-bottom: 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        color: #1e3a8a !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #ecfdf5 !important;
        border-left: 4px solid #10b981 !important;
        border-radius: 6px !important;
    }
    
    .stError {
        background-color: #fef2f2 !important;
        border-left: 4px solid #ef4444 !important;
        border-radius: 6px !important;
    }
    
    .stWarning {
        background-color: #fffbeb !important;
        border-left: 4px solid #f59e0b !important;
        border-radius: 6px !important;
    }
    
    .stInfo {
        background-color: #eff6ff !important;
        border-left: 4px solid #3b82f6 !important;
        border-radius: 6px !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 500 !important;
        font-size: 14px !important;
        color: #475569 !important;
    }
    
    /* Checkbox */
    .stCheckbox {
        font-size: 14px !important;
    }
    
    /* Remove extra spacing */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0 !important;
        border-color: #e2e8f0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    load_custom_css()  # Load custom styles
    
    st.title("OCRchestra")
    st.caption("Türkçe Derlem Analiz Aracı")
    
    # Show provider info (minimalist)
    
    # Show provider info
    client = get_llm_client()
    if client:
        provider = st.session_state.get('provider', 'Unknown')
        st.sidebar.success(f"✅ LLM Provider: {provider}")
    else:
        st.sidebar.error("❌ Groq API key gerekli")
        st.sidebar.info("Lütfen .streamlit/secrets.toml dosyasına GROQ_API_KEY ekleyin")

    # Tabs
    tab_library, tab_process, tab_corpus, tab_stats = st.tabs(["Kütüphane", "Yeni Ekle", "Derlem İncele", "İstatistikler"])

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
                    
                    # Advanced Concordance Search
                    st.subheader("Beriçim Analizi (KWIC)")
                    
                    # Import search engine
                    from ocrchestra.search_engine import CorpusSearchEngine
                    search = CorpusSearchEngine(db)
                    
                    # Query Builder
                    with st.expander("🔍 Gelişmiş Sorgu", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            search_type = st.selectbox(
                                "Arama Türü",
                                ["Kelime", "Lemma", "POS", "Gelişmiş"]
                            )
                        
                        with col2:
                            context_size = st.slider(
                                "Bağlam Boyutu (kelime)",
                                min_value=3,
                                max_value=20,
                                value=5
                            )
                        
                        # Search inputs based on type
                        if search_type == "Kelime":
                            keyword = st.text_input("Kelime veya Pattern", placeholder="örn: ayna, nöron.*")
                            col_a, col_b = st.columns(2)
                            use_regex = col_a.checkbox("Regex", value=False)
                            case_sens = col_b.checkbox("Büyük/küçük harf duyarlı", value=False)
                            
                        elif search_type == "Lemma":
                            keyword = st.text_input("Lemma (kök)", placeholder="örn: git, gel, göz")
                            use_regex = False
                            case_sens = st.checkbox("Büyük/küçük harf duyarlı", value=False)
                            
                        elif search_type == "POS":
                            # Get unique POS tags from document
                            if doc.get('analysis'):
                                import pandas as pd
                                df = pd.DataFrame(doc['analysis'])
                                pos_options = df['pos'].dropna().unique().tolist() if 'pos' in df.columns else []
                            else:
                                pos_options = []
                            
                            selected_pos = st.multiselect("POS Etiketleri", options=pos_options)
                            keyword = None
                            use_regex = False
                            case_sens = False
                            
                        else:  # Gelişmiş
                            keyword = st.text_input("Kelime Pattern (opsiyonel)", placeholder="nöron.*")
                            lemma_filter = st.text_input("Lemma (opsiyonel)", placeholder="göz")
                            
                            # POS filter
                            if doc.get('analysis'):
                                import pandas as pd
                                df = pd.DataFrame(doc['analysis'])
                                pos_options = df['pos'].dropna().unique().tolist() if 'pos' in df.columns else []
                            else:
                                pos_options = []
                            selected_pos = st.multiselect("POS Filtresi", options=pos_options)
                            
                            # Confidence filter
                            conf_range = st.slider(
                                "Güven Aralığı",
                                min_value=0.0,
                                max_value=1.0,
                                value=(0.0, 1.0),
                                step=0.1
                            )
                            
                            col_a, col_b = st.columns(2)
                            use_regex = col_a.checkbox("Regex", value=False)
                            case_sens = col_b.checkbox("Büyük/küçük harf duyarlı", value=False)
                    
                    # Execute search
                    if (search_type in ["Kelime", "Lemma"] and keyword) or \
                       (search_type == "POS" and selected_pos) or \
                       (search_type == "Gelişmiş" and (keyword or lemma_filter or selected_pos)):
                        
                        with st.spinner("Aranıyor..."):
                            # Perform search based on type
                            if search_type == "Kelime":
                                matches = search.search_word(
                                    keyword, 
                                    doc_id=doc_id, 
                                    regex=use_regex,
                                    case_sensitive=case_sens
                                )
                            elif search_type == "Lemma":
                                matches = search.search_lemma(
                                    keyword,
                                    doc_id=doc_id,
                                    case_sensitive=case_sens
                                )
                            elif search_type == "POS":
                                matches = search.search_pos(
                                    selected_pos,
                                    doc_id=doc_id
                                )
                            else:  # Gelişmiş
                                matches = search.complex_query(
                                    doc_id=doc_id,
                                    word_pattern=keyword if keyword else None,
                                    lemma=lemma_filter if lemma_filter else None,
                                    pos_tags=selected_pos if selected_pos else None,
                                    min_confidence=conf_range[0],
                                    max_confidence=conf_range[1],
                                    regex=use_regex,
                                    case_sensitive=case_sens
                                )
                            
                            # Generate concordance
                            if matches:
                                concordance = search.get_concordance(
                                    matches,
                                    doc_id=doc_id,
                                    context_words=context_size
                                )
                                
                                st.success(f"**{len(concordance)}** eşleşme bulundu")
                                
                                # Display as table
                                import pandas as pd
                                conc_df = pd.DataFrame(concordance)
                                
                                st.dataframe(
                                    conc_df[['left', 'center', 'right', 'lemma', 'pos', 'confidence']],
                                    use_container_width=True,
                                    column_config={
                                        "left": "Sol Bağlam",
                                        "center": st.column_config.TextColumn("Anahtar", width="small"),
                                        "right": "Sağ Bağlam",
                                        "lemma": "Lemma",
                                        "pos": "POS",
                                        "confidence": st.column_config.ProgressColumn(
                                            "Güven",
                                            format="%.2f",
                                            min_value=0,
                                            max_value=1
                                        )
                                    }
                                )
                                
                                # Export button
                                csv = conc_df.to_csv(index=False)
                                st.download_button(
                                    "📥 CSV İndir",
                                    csv,
                                    file_name=f"concordance_{doc['filename']}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.info("Eşleşme bulunamadı")
                    
                    st.divider()
                    
                    # Analysis Viewer
                    st.subheader("Dilbilimsel Analiz")
                    
                    if doc.get('analysis'):
                        analysis_data = doc['analysis']
                        import pandas as pd
                        df = pd.DataFrame(analysis_data)
                        
                        # Create sub-tabs for analysis views
                        analysis_tabs = st.tabs(["İstatistikler", "Tablo Görünümü", "Metin Görünümü", "Manuel Düzeltme"])
                        
                        with analysis_tabs[0]:  # Statistics tab
                            # --- 1. Statistics Cards ---
                            st.markdown("### İstatistikler")
                        
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
                        st.markdown("### Filtreler")
                        
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
                        st.markdown("### Metin Görselleştirmesi")
                        st.caption("Kelime türleri ince renklerle işaretlenmiştir. ⚠ düşük güvenli etiketleri gösterir.")

                        # Minimal Academic Color Mapping
                        pos_colors = {
                            "NOUN": "#3b82f6",  # Blue
                            "VERB": "#64748b",  # Slate
                            "ADJ": "#10b981",   # Emerald
                            "ADV": "#8b5cf6",   # Violet
                            "PRON": "#f59e0b",  # Amber
                            "DET": "#6b7280",   # Gray
                            "ADP": "#6b7280",   # Gray
                            "NUM": "#06b6d4",   # Cyan
                            "PUNCT": "#94a3b8",  # Light slate
                            "CONJ": "#a855f7"   # Purple
                        }

                        html_output = '<div style="line-height: 2.2; padding: 1.5rem; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">'
                        
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

                            color = pos_colors.get(pos, "#94a3b8")
                            
                            # Build tooltip with confidence info
                            tooltip = f"Lemma: {lemma} | POS: {pos} | Güven: {confidence:.2f}"
                            if warning:
                                tooltip += f" | {warning}"
                            
                            # Add warning indicator for low confidence
                            display_word = word
                            warn_indicator = ""
                            if needs_review or confidence < 0.6:
                                warn_indicator = '<span style="color: #f59e0b; font-size: 10px; vertical-align: super;">⚠</span>'
                            
                            # Minimal styling with subtle border-bottom
                            html_output += (
                                f'<span style="'
                                f'color: #0f172a; '
                                f'padding: 2px 4px; '
                                f'margin: 0 1px; '
                                f'border-bottom: 2px solid {color}; '
                                f'font-size: 15px;" '
                                f'title="{tooltip}">{display_word}{warn_indicator}</span> '
                            )
                        
                        if len(analysis_data) > vis_limit:
                            html_output += f'<br><br><em style="color: #64748b;">... ({len(analysis_data) - vis_limit} kelime daha) ...</em>'
                        
                        html_output += '</div>'
                        
                        st.markdown(html_output, unsafe_allow_html=True)
                        
                        # Minimal legend
                        st.caption("İsim • Fiil • Sıfat • Zarf • Zamir | ⚠ İnceleme gerekli")

                    else:
                        st.info("Bu belge için POS/Lemma analizi yapılmamış.")

                    with st.expander("Ham Metni Göster"):
                        st.text_area("Metin", doc['cleaned_text'], height=300)

    # Statistics tab content loaded from external file for readability
    with tab_stats:
        st.header("Derlem İstatistikleri")
        docs = db.get_all_documents()
        processed_docs = [d for d in docs if d['processed']]
        
        if not processed_docs:
            st.warning("Henüz işlenmiş belge yok.")
        else:
            # Document selection and statistics display
            # Full implementation in separate module to keep app.py clean
            exec(open('stats_tab.txt').read())

if __name__ == "__main__":
    main()
