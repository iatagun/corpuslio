"""Export corpus data to various formats.

Supports:
- CoNLL-U (Universal Dependencies)
- JSON
- CSV
- VRT (CWB/SketchEngine)
"""
from typing import List, Dict, Any
import json
import csv
from io import StringIO


class CorpusExporter:
    """Export corpus annotations to different formats."""

    def __init__(self, analysis_data: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """Initialize exporter.

        Args:
            analysis_data: List of annotated tokens
            metadata: Optional document metadata
        """
        self.data = [item for item in analysis_data if isinstance(item, dict)]
        self.metadata = metadata or {}

    def to_json(self, pretty: bool = True) -> str:
        """Export to JSON format.

        Args:
            pretty: Pretty print JSON

        Returns:
            JSON string
        """
        output = {
            'metadata': self.metadata,
            'tokens': self.data
        }
        
        if pretty:
            return json.dumps(output, ensure_ascii=False, indent=2)
        else:
            return json.dumps(output, ensure_ascii=False)

    def to_csv(self) -> str:
        """Export to CSV format.

        Returns:
            CSV string
        """
        output = StringIO()
        
        if not self.data:
            return ""
        
        # Determine fields
        fields = ['word', 'lemma', 'pos', 'confidence']
        
        # Check if morphology exists
        has_morph = any('morphology' in item and item['morphology'] for item in self.data)
        
        if has_morph:
            fields.append('morphology')
        
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        
        for item in self.data:
            row = {k: item.get(k, '') for k in fields}
            
            # Serialize morphology
            if has_morph and 'morphology' in row:
                morph = item.get('morphology', {})
                if morph:
                    row['morphology'] = '|'.join(f"{k}={v}" for k, v in morph.items())
                else:
                    row['morphology'] = ''
            
            writer.writerow(row)
        
        return output.getvalue()

    def to_conllu(self) -> str:
        """Export to CoNLL-U format (Universal Dependencies).

        Format:
        # sent_id = 1
        # text = ...
        1    word    lemma    POS    ...    morphology    ...

        Returns:
            CoNLL-U formatted string
        """
        output = []
        
        # Metadata
        if self.metadata:
            output.append(f"# newdoc id = {self.metadata.get('filename', 'unknown')}")
        
        # For simplicity, treat entire text as one sentence
        # In production, you'd need sentence boundary detection
        sent_id = 1
        output.append(f"# sent_id = {sent_id}")
        
        # Reconstruct text
        text = ' '.join(item.get('word', '') for item in self.data)
        output.append(f"# text = {text}")
        
        # Token lines
        for idx, item in enumerate(self.data, 1):
            word = item.get('word', '_')
            lemma = item.get('lemma', '_')
            upos = item.get('pos', '_')
            xpos = '_'  # Language-specific POS
            feats = self._format_morphology(item.get('morphology', {}))
            head = '_'  # Dependency head (not implemented)
            deprel = '_'  # Dependency relation
            deps = '_'  # Enhanced dependencies
            misc = f"Confidence={item.get('confidence', 1.0):.2f}"
            
            line = f"{idx}\t{word}\t{lemma}\t{upos}\t{xpos}\t{feats}\t{head}\t{deprel}\t{deps}\t{misc}"
            output.append(line)
        
        output.append("")  # Empty line after sentence
        
        return '\n'.join(output)

    def to_vrt(self, include_structure: bool = True) -> str:
        """Export to VRT format (CWB/SketchEngine).

        Format:
        <doc id="..." filename="..." ...>
        <p id="p1">
        <s id="s1">
        word    lemma    pos    morphology
        </s>
        </p>
        </doc>

        Args:
            include_structure: Include <p> and <s> tags

        Returns:
            VRT formatted string
        """
        output = []
        
        # Document element with metadata
        doc_attrs = ' '.join(f'{k}="{v}"' for k, v in self.metadata.items() if v)
        output.append(f"<doc {doc_attrs}>")
        
        if include_structure and self.data:
            # Try to detect sentence boundaries
            from corpuslio.sentence_detector import SentenceBoundaryDetector
            
            detector = SentenceBoundaryDetector()
            
            # Reconstruct text from tokens
            text = ' '.join(item.get('word', '') for item in self.data)
            
            # Add sentence IDs to tokens
            tokens_with_sent = detector.annotate_tokens(self.data.copy(), text)
            
            # Group by sentence
            current_sent_id = None
            current_para_id = 1  # Simple: one paragraph for now
            
            output.append(f"<p id=\"p{current_para_id}\">")
            
            for item in tokens_with_sent:
                sent_id = item.get('sent_id', 1)
                
                # New sentence
                if sent_id != current_sent_id:
                    # Close previous sentence
                    if current_sent_id is not None:
                        output.append("</s>")
                    
                    # Open new sentence
                    output.append(f"<s id=\"s{sent_id}\">")
                    current_sent_id = sent_id
                
                # Token line
                word = item.get('word', '')
                lemma = item.get('lemma', '')
                pos = item.get('pos', '')
                morph = self._format_morphology_vrt(item.get('morphology', {}))
                
                line = f"{word}\t{lemma}\t{pos}\t{morph}"
                output.append(line)
            
            # Close last sentence and paragraph
            if current_sent_id is not None:
                output.append("</s>")
            output.append("</p>")
        
        else:
            # Simple mode: no structure tags
            output.append("<s>")
            for item in self.data:
                word = item.get('word', '')
                lemma = item.get('lemma', '')
                pos = item.get('pos', '')
                morph = self._format_morphology_vrt(item.get('morphology', {}))
                
                line = f"{word}\t{lemma}\t{pos}\t{morph}"
                output.append(line)
            output.append("</s>")
        
        output.append("</doc>")
        
        return '\n'.join(output)


    def _format_morphology(self, morph: Dict[str, str]) -> str:
        """Format morphology for CoNLL-U.

        Args:
            morph: Morphology dict

        Returns:
            Pipe-separated features or '_'
        """
        if not morph:
            return '_'
        
        # Sort features alphabetically (CoNLL-U convention)
        features = sorted(f"{k}={v}" for k, v in morph.items())
        return '|'.join(features)

    def _format_morphology_vrt(self, morph: Dict[str, str]) -> str:
        """Format morphology for VRT.

        Args:
            morph: Morphology dict

        Returns:
            Comma-separated features or '-'
        """
        if not morph:
            return '-'
        
        features = [f"{k}={v}" for k, v in morph.items()]
        return ','.join(features)
