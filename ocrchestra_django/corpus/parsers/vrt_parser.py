"""VRT (Verticalized Text) format parser for Corpus Workbench.

VRT Format Specification:
https://www.sketchengine.eu/documentation/corpus-formats/

Format:
- XML-like structural tags: <text>, <p>, <s>, etc.
- Opening tags can have attributes: <text author="..." date="...">
- Token lines are tab-separated: WORD\tLEMMA\tPOS\t...
- Closing tags: </s>, </p>, </text>
- Comments start with <!-- -->

Example:
<text author="Orhan Pamuk" date="2000" genre="novel">
<p id="1">
<s id="1">
Kış\tkış\tNOUN\tCase=Nom|Number=Sing
geldi\tgel\tVERB\tAspect=Perf|Mood=Ind|Number=Sing|Person=3|Polarity=Pos|Tense=Past
.\t.\tPUNCT\t_
</s>
</p>
</text>
"""

import re
import hashlib
from typing import Dict, List, Tuple, Optional
from xml.etree import ElementTree as ET
from django.db import transaction
from corpus.models import Document, Sentence, Token, CorpusMetadata


class VRTParser:
    """Parse VRT (Verticalized Text) format corpus files."""
    
    def __init__(self, filepath: str, user=None):
        """Initialize parser.
        
        Args:
            filepath: Path to VRT file
            user: Django User object (for import tracking)
        """
        self.filepath = filepath
        self.user = user
        self.global_metadata = {}
        self.structural_annotations = {}
        self.sentences = []
        self.stats = {
            'sentence_count': 0,
            'token_count': 0,
            'unique_forms': set(),
            'unique_lemmas': set(),
        }
        
        # Column configuration (can be customized per corpus)
        self.columns = ['form', 'lemma', 'pos']  # Default, will auto-detect
    
    def parse(self) -> Dict:
        """Parse entire VRT file.
        
        Returns:
            Dict with parsing results and statistics
        """
        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Calculate file hash
        file_hash = hashlib.sha256(content.encode()).hexdigest()
        
        lines = content.strip().split('\n')
        
        current_sentence = None
        current_sentence_text = []
        current_sentence_tokens = []
        current_metadata = {}
        text_metadata = {}
        para_metadata = {}
        
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            
            if not line or line.startswith('<!--'):
                continue  # Skip empty lines and comments
            
            # Opening tag
            if line.startswith('<') and not line.startswith('</'):
                tag, attrs = self._parse_opening_tag(line)
                
                if tag == 'text':
                    text_metadata = attrs
                    self.global_metadata = attrs
                elif tag == 'p':
                    para_metadata = attrs
                elif tag == 's':
                    current_metadata = {**text_metadata, **para_metadata, **attrs}
                    current_sentence_text = []
                    current_sentence_tokens = []
                
                continue
            
            # Closing tag
            if line.startswith('</'):
                tag = line[2:-1]
                
                if tag == 's':
                    # End of sentence
                    if current_sentence_tokens:
                        sentence_data = {
                            'metadata': current_metadata,
                            'text': ' '.join(current_sentence_text),
                            'tokens': current_sentence_tokens,
                        }
                        self.sentences.append(sentence_data)
                        self.stats['sentence_count'] += 1
                    
                    current_sentence_text = []
                    current_sentence_tokens = []
                    current_metadata = {}
                elif tag == 'p':
                    para_metadata = {}
                elif tag == 'text':
                    text_metadata = {}
                
                continue
            
            # Token line
            if '\t' in line:
                token_data = self._parse_token_line(line, len(current_sentence_tokens) + 1)
                if token_data:
                    current_sentence_tokens.append(token_data)
                    current_sentence_text.append(token_data['form'])
                    self.stats['token_count'] += 1
                    self.stats['unique_forms'].add(token_data['form'].lower())
                    if token_data.get('lemma'):
                        self.stats['unique_lemmas'].add(token_data['lemma'].lower())
        
        return {
            'file_hash': file_hash,
            'global_metadata': self.global_metadata,
            'structural_annotations': self.structural_annotations,
            'sentences': self.sentences,
            'stats': {
                'sentence_count': self.stats['sentence_count'],
                'token_count': self.stats['token_count'],
                'unique_forms': len(self.stats['unique_forms']),
                'unique_lemmas': len(self.stats['unique_lemmas']),
            }
        }
    
    def _parse_opening_tag(self, line: str) -> Tuple[str, Dict]:
        """Parse opening XML-like tag and extract attributes.
        
        Args:
            line: Tag line like <text author="..." date="...">
        
        Returns:
            Tuple of (tag_name, attributes_dict)
        """
        # Remove < and >
        line = line[1:-1]
        
        # Split tag name and attributes
        parts = line.split(None, 1)
        tag_name = parts[0]
        
        attrs = {}
        if len(parts) > 1:
            # Parse attributes (key="value" or key='value')
            attr_pattern = r'(\w+)=["\']([^"\']*)["\']'
            matches = re.findall(attr_pattern, parts[1])
            attrs = dict(matches)
        
        return tag_name, attrs
    
    def _parse_token_line(self, line: str, index: int) -> Optional[Dict]:
        """Parse token line with tab-separated fields.
        
        Args:
            line: Tab-separated token line
            index: Token index in sentence
        
        Returns:
            Dict with token data
        """
        fields = line.split('\t')
        
        if not fields:
            return None
        
        # Auto-detect columns from first token
        if len(self.columns) < len(fields):
            # Extend columns if needed
            for i in range(len(self.columns), len(fields)):
                self.columns.append(f'attr_{i}')
        
        token_data = {'index': index}
        vrt_attributes = {}
        
        for i, value in enumerate(fields):
            if i < len(self.columns):
                col_name = self.columns[i]
                
                # Map to standard fields
                if col_name == 'form':
                    token_data['form'] = value
                elif col_name == 'lemma':
                    token_data['lemma'] = value if value != '_' else ''
                elif col_name in ('pos', 'upos', 'tag'):
                    token_data['upos'] = value if value != '_' else ''
                else:
                    # Store as VRT attribute
                    vrt_attributes[col_name] = value
        
        token_data['vrt_attributes'] = vrt_attributes
        
        # Ensure form exists
        if 'form' not in token_data:
            token_data['form'] = fields[0]
        
        return token_data
    
    @transaction.atomic
    def import_to_database(self, document: Document) -> CorpusMetadata:
        """Import parsed VRT data to database.
        
        Args:
            document: Document instance to attach corpus data to
        
        Returns:
            Created CorpusMetadata instance
        """
        # Parse file
        parse_result = self.parse()
        
        # Check for duplicates
        existing = CorpusMetadata.objects.filter(
            file_hash=parse_result['file_hash']
        ).first()
        if existing:
            raise ValueError(f"File already imported: {existing.document.filename}")
        
        # Create corpus metadata
        metadata = CorpusMetadata.objects.create(
            document=document,
            source_format='vrt',
            global_metadata=parse_result['global_metadata'],
            structural_annotations=parse_result['structural_annotations'],
            imported_by=self.user,
            original_filename=self.filepath,
            file_hash=parse_result['file_hash'],
            sentence_count=parse_result['stats']['sentence_count'],
            unique_lemmas=parse_result['stats']['unique_lemmas'],
            unique_forms=parse_result['stats']['unique_forms'],
        )
        
        # Import sentences and tokens
        for sent_idx, sent_data in enumerate(parse_result['sentences'], start=1):
            sentence = Sentence.objects.create(
                document=document,
                index=sent_idx,
                text=sent_data['text'],
                token_count=len(sent_data['tokens']),
                metadata=sent_data['metadata'],
            )
            
            # Bulk create tokens
            token_objects = [
                Token(
                    document=document,
                    sentence=sentence,
                    index=token['index'],
                    form=token['form'],
                    lemma=token.get('lemma', ''),
                    upos=token.get('upos', ''),
                    vrt_attributes=token.get('vrt_attributes', {}),
                )
                for token in sent_data['tokens']
            ]
            Token.objects.bulk_create(token_objects)
        
        # Update document statistics
        document.token_count = parse_result['stats']['token_count']
        document.processed = True
        
        # Extract metadata to document fields if available
        if 'author' in parse_result['global_metadata']:
            document.author = parse_result['global_metadata']['author']
        if 'genre' in parse_result['global_metadata']:
            document.genre = parse_result['global_metadata']['genre']
        if 'date' in parse_result['global_metadata']:
            try:
                from datetime import datetime
                date_str = parse_result['global_metadata']['date']
                # Try to parse date (YYYY-MM-DD or YYYY)
                if '-' in date_str:
                    document.document_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    document.document_date = datetime.strptime(date_str, '%Y').date()
            except:
                pass
        
        document.save()
        
        return metadata
