"""CoNLL-U format parser for Universal Dependencies corpora.

CoNLL-U Format Specification:
https://universaldependencies.org/format.html

Format:
- Lines starting with # are comments (metadata)
- Blank lines separate sentences
- Token lines have 10 tab-separated fields:
  1. ID: Word index (integer starting at 1, or range for multiword tokens)
  2. FORM: Word form or punctuation symbol
  3. LEMMA: Lemma or stem of word form
  4. UPOS: Universal part-of-speech tag
  5. XPOS: Language-specific part-of-speech tag
  6. FEATS: Morphological features ("|"-separated)
  7. HEAD: Head of the current word (index or 0 for root)
  8. DEPREL: Universal dependency relation to the HEAD
  9. DEPS: Enhanced dependency graph
  10. MISC: Any other annotation
"""

import re
import hashlib
from typing import Dict, List, Tuple, Optional
from django.db import transaction
from corpus.models import Document, Sentence, Token, CorpusMetadata


class CoNLLUParser:
    """Parse CoNLL-U format corpus files."""
    
    def __init__(self, filepath: str, user=None):
        """Initialize parser.
        
        Args:
            filepath: Path to CoNLL-U file
            user: Django User object (for import tracking)
        """
        self.filepath = filepath
        self.user = user
        self.global_metadata = {}
        self.sentences = []
        self.stats = {
            'sentence_count': 0,
            'token_count': 0,
            'unique_forms': set(),
            'unique_lemmas': set(),
        }
    
    def parse(self) -> Dict:
        """Parse entire CoNLL-U file.
        
        Returns:
            Dict with parsing results and statistics
        """
        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Calculate file hash for duplicate detection
        file_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Split into sentence blocks
        sentence_blocks = content.strip().split('\n\n')
        
        for block in sentence_blocks:
            if not block.strip():
                continue
            
            sentence_data = self._parse_sentence_block(block)
            if sentence_data:
                self.sentences.append(sentence_data)
                self.stats['sentence_count'] += 1
        
        return {
            'file_hash': file_hash,
            'global_metadata': self.global_metadata,
            'sentences': self.sentences,
            'stats': {
                'sentence_count': self.stats['sentence_count'],
                'token_count': self.stats['token_count'],
                'unique_forms': len(self.stats['unique_forms']),
                'unique_lemmas': len(self.stats['unique_lemmas']),
            }
        }
    
    def _parse_sentence_block(self, block: str) -> Optional[Dict]:
        """Parse single sentence block.
        
        Args:
            block: Text block for one sentence
        
        Returns:
            Dict with sentence metadata and tokens
        """
        lines = block.strip().split('\n')
        
        metadata = {}
        tokens = []
        text = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Comment line (metadata)
            if line.startswith('#'):
                key, value = self._parse_comment(line)
                if key == 'text':
                    text = value
                elif key == 'global':
                    # Global metadata (document-level)
                    parts = value.split('=', 1)
                    if len(parts) == 2:
                        self.global_metadata[parts[0].strip()] = parts[1].strip()
                else:
                    metadata[key] = value
                continue
            
            # Token line
            fields = line.split('\t')
            if len(fields) != 10:
                continue  # Skip malformed lines
            
            # Skip multiword tokens (1-2, 3-4, etc.)
            if '-' in fields[0] or '.' in fields[0]:
                continue
            
            try:
                token_id = int(fields[0])
            except ValueError:
                continue  # Skip empty nodes
            
            token_data = {
                'index': token_id,
                'form': fields[1],
                'lemma': fields[2] if fields[2] != '_' else '',
                'upos': fields[3] if fields[3] != '_' else '',
                'xpos': fields[4] if fields[4] != '_' else '',
                'feats': fields[5] if fields[5] != '_' else '',
                'head': int(fields[6]) if fields[6] != '_' else None,
                'deprel': fields[7] if fields[7] != '_' else '',
                'deps': fields[8] if fields[8] != '_' else '',
                'misc': fields[9] if fields[9] != '_' else '',
            }
            
            tokens.append(token_data)
            self.stats['token_count'] += 1
            self.stats['unique_forms'].add(token_data['form'].lower())
            if token_data['lemma']:
                self.stats['unique_lemmas'].add(token_data['lemma'].lower())
        
        if not tokens:
            return None
        
        # Reconstruct text if not provided
        if not text:
            text = self._reconstruct_text(tokens)
        
        return {
            'metadata': metadata,
            'text': text,
            'tokens': tokens,
        }
    
    def _parse_comment(self, line: str) -> Tuple[str, str]:
        """Parse comment line.
        
        Args:
            line: Comment line starting with #
        
        Returns:
            Tuple of (key, value)
        """
        line = line[1:].strip()  # Remove #
        
        # Standard CoNLL-U comments: # key = value
        if '=' in line:
            parts = line.split('=', 1)
            return parts[0].strip(), parts[1].strip()
        
        # Other comments
        return 'comment', line
    
    def _reconstruct_text(self, tokens: List[Dict]) -> str:
        """Reconstruct sentence text from tokens.
        
        Args:
            tokens: List of token dictionaries
        
        Returns:
            Reconstructed sentence text
        """
        words = []
        for token in tokens:
            words.append(token['form'])
            
            # Check MISC field for SpaceAfter=No
            if 'SpaceAfter=No' not in token.get('misc', ''):
                words.append(' ')
        
        return ''.join(words).strip()
    
    @transaction.atomic
    def import_to_database(self, document: Document) -> CorpusMetadata:
        """Import parsed data to database.
        
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
            source_format='conllu',
            global_metadata=parse_result['global_metadata'],
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
                    lemma=token['lemma'],
                    upos=token['upos'],
                    xpos=token['xpos'],
                    feats=token['feats'],
                    head=token['head'],
                    deprel=token['deprel'],
                    deps=token['deps'],
                    misc=token['misc'],
                )
                for token in sent_data['tokens']
            ]
            Token.objects.bulk_create(token_objects)
        
        # Update document statistics
        document.token_count = parse_result['stats']['token_count']
        document.processed = True
        document.save()
        
        return metadata
