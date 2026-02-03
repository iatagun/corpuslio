"""Annotation editor for manual correction of linguistic annotations.

Provides:
- Inline editing interface
- Bulk correction tools
- Annotation history tracking
"""
from typing import List, Dict, Any, Optional
import streamlit as st
from datetime import datetime


def render_annotation_editor(analysis_data: List[Dict[str, Any]], doc_id: int, db_manager):
    """Render inline annotation editor.
    
    Args:
        analysis_data: List of annotations
        doc_id: Document ID
        db_manager: DatabaseManager instance
    """
    st.subheader("Manuel Düzeltme Arayüzü")
    st.caption("Hatalı etiketleri düzeltmek için kelimeye tıklayın")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        show_only_flagged = st.checkbox("Sadece işaretlileri göster", value=True)
    with col2:
        sort_by_conf = st.checkbox("Güvene göre sırala", value=True)
    
    # Filter and sort
    items_to_edit = [item for item in analysis_data if isinstance(item, dict)]
    
    if show_only_flagged:
        items_to_edit = [item for item in items_to_edit if item.get('needs_review', False) or item.get('confidence', 1.0) < 0.6]
    
    if sort_by_conf:
        items_to_edit.sort(key=lambda x: x.get('confidence', 1.0))
    
    if not items_to_edit:
        st.info("Düzeltilecek öğe yok")
        return
    
    st.write(f"**{len(items_to_edit)}** öğe düzeltme için hazır")
    
    # Pagination
    items_per_page = 20
    total_pages = (len(items_to_edit) + items_per_page - 1) // items_per_page
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    
    page = st.session_state.current_page
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(items_to_edit))
    
    # Display items for editing
    for idx, item in enumerate(items_to_edit[start_idx:end_idx], start=start_idx):
        with st.expander(
            f"⚠ {item.get('word', '')} → {item.get('lemma', '')} ({item.get('pos', '')}) "
            f"[Güven: {item.get('confidence', 0):.2f}]",
            expanded=False
        ):
            col_word, col_lemma, col_pos, col_conf = st.columns(4)
            
            # Edit fields
            with col_word:
                new_word = st.text_input("Kelime", value=item.get('word', ''), key=f"word_{idx}")
            
            with col_lemma:
                new_lemma = st.text_input("Lemma", value=item.get('lemma', ''), key=f"lemma_{idx}")
            
            with col_pos:
                pos_options = ['NOUN', 'VERB', 'ADJ', 'ADV', 'PRON', 'DET', 'ADP', 'NUM', 'CONJ', 'PUNCT', 'PROPN']
                current_pos = item.get('pos', 'NOUN')
                new_pos = st.selectbox(
                    "POS",
                    options=pos_options,
                    index=pos_options.index(current_pos) if current_pos in pos_options else 0,
                    key=f"pos_{idx}"
                )
            
            with col_conf:
                new_conf = st.slider(
                    "Güven",
                    0.0, 1.0,
                    value=float(item.get('confidence', 0.5)),
                    step=0.05,
                    key=f"conf_{idx}"
                )
            
            # Morphology editor (if present)
            if 'morphology' in item and item['morphology']:
                st.caption("Morfolojik Özellikler")
                morph = item['morphology']
                
                morph_cols = st.columns(3)
                with morph_cols[0]:
                    if 'Case' in morph:
                        st.text(f"Case: {morph['Case']}")
                    if 'Number' in morph:
                        st.text(f"Number: {morph['Number']}")
                with morph_cols[1]:
                    if 'Tense' in morph:
                        st.text(f"Tense: {morph['Tense']}")
                    if 'Person' in morph:
                        st.text(f"Person: {morph['Person']}")
                with morph_cols[2]:
                    if 'Voice' in morph:
                        st.text(f"Voice: {morph['Voice']}")
                    if 'Polarity' in morph:
                        st.text(f"Polarity: {morph['Polarity']}")
            
            # Action buttons
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
            with btn_col1:
                if st.button("✅ Kaydet", key=f"save_{idx}"):
                    # Update item
                    item['word'] = new_word
                    item['lemma'] = new_lemma
                    item['pos'] = new_pos
                    item['confidence'] = new_conf
                    item['needs_review'] = False  # Mark as reviewed
                    
                    # Save to database
                    db_manager.save_results(doc_id, None, None, analysis_data)
                    st.success("Kaydedildi!")
                    st.rerun()
            
            with btn_col2:
                if st.button("✓ Onayla", key=f"approve_{idx}"):
                    item['confidence'] = 1.0
                    item['needs_review'] = False
                    db_manager.save_results(doc_id, None, None, analysis_data)
                    st.success("Onaylandı!")
                    st.rerun()
    
    # Pagination controls
    st.divider()
    pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
    
    with pcol1:
        if st.button("◀ Önceki", disabled=(page == 0)):
            st.session_state.current_page -= 1
            st.rerun()
    
    with pcol2:
        st.write(f"Sayfa {page + 1} / {total_pages}")
    
    with pcol3:
        if st.button("Sonraki ▶", disabled=(page >= total_pages - 1)):
            st.session_state.current_page += 1
            st.rerun()


def render_bulk_editor(analysis_data: List[Dict[str, Any]], doc_id: int, db_manager):
    """Render bulk correction interface.
    
    Args:
        analysis_data: List of annotations
        doc_id: Document ID
        db_manager: DatabaseManager instance
    """
    st.subheader("Toplu Düzeltme")
    
    # Find and replace
    st.markdown("### Bul ve Değiştir")
    
    col1, col2 = st.columns(2)
    with col1:
        find_field = st.selectbox("Alan", ["lemma", "pos"])
        find_value = st.text_input("Aranan değer")
    
    with col2:
        replace_value = st.text_input("Yeni değer")
    
    if st.button("🔄 Toplu Değiştir"):
        if find_value and replace_value:
            count = 0
            for item in analysis_data:
                if isinstance(item, dict) and item.get(find_field) == find_value:
                    item[find_field] = replace_value
                    count += 1
            
            if count > 0:
                db_manager.save_results(doc_id, None, None, analysis_data)
                st.success(f"{count} öğe güncellendi!")
                st.rerun()
            else:
                st.info("Eşleşme bulunamadı")
    
    st.divider()
    
    # Bulk approve
    st.markdown("### Toplu Onaylama")
    
    min_conf_approve = st.slider("Minimum güven skoru", 0.0, 1.0, 0.8, 0.05)
    
    if st.button("✅ Yüksek güvenli öğeleri toplu onayla"):
        count = 0
        for item in analysis_data:
            if isinstance(item, dict) and item.get('confidence', 0) >= min_conf_approve:
                item['needs_review'] = False
                item['confidence'] = 1.0
                count += 1
        
        if count > 0:
            db_manager.save_results(doc_id, None, None, analysis_data)
            st.success(f"{count} öğe onaylandı!")
            st.rerun()
