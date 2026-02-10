"""
CoNLL-U Format Parser and Serializer

Implements parsing and serialization for CoNLL-U format (Universal Dependencies).
Specification: https://universaldependencies.org/format.html

CoNLL-U format has 10 tab-separated columns:
1. ID - Word index (integer or range for multi-word tokens)
2. FORM - Word form (surface text)
3. LEMMA - Lemma or stem
4. UPOS - Universal part-of-speech tag
5. XPOS - Language-specific part-of-speech tag
6. FEATS - Morphological features (Feature=Value pairs)
7. HEAD - Head of the current word (dependency parent index, 0 for root)
8. DEPREL - Dependency relation to HEAD
9. DEPS - Enhanced dependency graph
10. MISC - Any other annotation

Example:
# text = Bu bir test cümlesidir.
1	Bu	bu	DET	Det	_	4	det	_	_
2	bir	bir	DET	Det	_	4	det	_	_
3	test	test	NOUN	Noun	Case=Nom	4	nmod	_	_
4	cümlesidir	cümle	NOUN	Noun	Case=Nom|Polarity=Pos	0	root	_	SpaceAfter=No
5	.	.	PUNCT	Punc	_	4	punct	_	_
"""

from typing import List, Dict, Optional, Tuple
import re


class CoNLLUParser:
    """Parser for CoNLL-U format dependency annotations."""
    
    # Column names in CoNLL-U format
    COLUMNS = [
        'id', 'form', 'lemma', 'upos', 'xpos',
        'feats', 'head', 'deprel', 'deps', 'misc'
    ]
    
    @staticmethod
    def parse(conllu_text: str) -> List[Dict]:
        """
        Parse CoNLL-U formatted text into list of token dictionaries.
        
        Args:
            conllu_text: String containing CoNLL-U formatted data
            
        Returns:
            List of token dictionaries with parsed fields
            
        Example:
            >>> text = "1\\tBu\\tbu\\tDET\\tDet\\t_\\t4\\tdet\\t_\\t_"
            >>> tokens = CoNLLUParser.parse(text)
            >>> tokens[0]['form']
            'Bu'
        """
        tokens = []
        sentence_id = 0
        sentence_text = None
        
        for line in conllu_text.strip().split('\n'):
            line = line.strip()
            
            # Skip empty lines (sentence boundaries)
            if not line:
                sentence_id += 1
                sentence_text = None
                continue
            
            # Handle comment lines
            if line.startswith('#'):
                # Extract sentence text from comment
                if line.startswith('# text = '):
                    sentence_text = line[9:].strip()
                continue
            
            # Skip multi-word tokens (e.g., "1-2	yapıyorum	_	_...")
            if '-' in line.split('\t')[0]:
                continue
            
            # Skip empty nodes (e.g., "1.1	_	_...")
            if '.' in line.split('\t')[0]:
                continue
            
            # Parse token line
            try:
                token = CoNLLUParser._parse_token_line(line, sentence_id, sentence_text)
                tokens.append(token)
            except Exception as e:
                # Log error but continue parsing
                print(f"Warning: Failed to parse line: {line[:50]}... Error: {e}")
                continue
        
        return tokens
    
    @staticmethod
    def _parse_token_line(line: str, sentence_id: int, sentence_text: Optional[str]) -> Dict:
        """Parse a single token line into a dictionary."""
        fields = line.split('\t')
        
        if len(fields) != 10:
            raise ValueError(f"Expected 10 fields, got {len(fields)}")
        
        # Parse ID (should be integer)
        try:
            token_id = int(fields[0])
        except ValueError:
            raise ValueError(f"Invalid token ID: {fields[0]}")
        
        # Parse HEAD (should be integer)
        try:
            head = int(fields[6]) if fields[6] != '_' else 0
        except ValueError:
            head = 0
        
        # Parse features (Key=Value|Key=Value format)
        feats = CoNLLUParser._parse_features(fields[5])
        
        # Parse misc (Key=Value format)
        misc = CoNLLUParser._parse_features(fields[9])
        
        token = {
            'id': token_id,
            'form': fields[1] if fields[1] != '_' else '',
            'lemma': fields[2] if fields[2] != '_' else '',
            'upos': fields[3] if fields[3] != '_' else '',
            'xpos': fields[4] if fields[4] != '_' else '',
            'feats': feats,
            'head': head,
            'deprel': fields[7] if fields[7] != '_' else '',
            'deps': fields[8] if fields[8] != '_' else None,
            'misc': misc,
            'sentence_id': sentence_id
        }
        
        if sentence_text:
            token['sentence_text'] = sentence_text
        
        return token
    
    @staticmethod
    def _parse_features(feat_string: str) -> Dict:
        """
        Parse feature string into dictionary.
        
        Examples:
            "Case=Nom|Number=Sing" -> {'Case': 'Nom', 'Number': 'Sing'}
            "_" -> {}
        """
        if feat_string == '_' or not feat_string:
            return {}
        
        features = {}
        for pair in feat_string.split('|'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                features[key] = value
        
        return features
    
    @staticmethod
    def serialize(tokens: List[Dict], include_metadata: bool = True) -> str:
        """
        Convert list of token dictionaries to CoNLL-U format string.
        
        Args:
            tokens: List of token dictionaries
            include_metadata: Whether to include comment lines (# text = ...)
            
        Returns:
            CoNLL-U formatted string
            
        Example:
            >>> tokens = [{'id': 1, 'form': 'Bu', 'lemma': 'bu', ...}]
            >>> conllu = CoNLLUParser.serialize(tokens)
        """
        if not tokens:
            return ""
        
        lines = []
        current_sentence_id = None
        
        for token in tokens:
            sentence_id = token.get('sentence_id', 0)
            
            # Add sentence boundary and metadata
            if sentence_id != current_sentence_id:
                if current_sentence_id is not None:
                    lines.append('')  # Empty line between sentences
                
                if include_metadata and 'sentence_text' in token:
                    lines.append(f"# text = {token['sentence_text']}")
                
                current_sentence_id = sentence_id
            
            # Serialize token
            token_line = CoNLLUParser._serialize_token(token)
            lines.append(token_line)
        
        return '\n'.join(lines) + '\n'
    
    @staticmethod
    def _serialize_token(token: Dict) -> str:
        """Serialize a single token to CoNLL-U line format."""
        fields = []
        
        # ID
        fields.append(str(token.get('id', 1)))
        
        # FORM
        fields.append(token.get('form', '_'))
        
        # LEMMA
        fields.append(token.get('lemma', '_'))
        
        # UPOS
        fields.append(token.get('upos', '_'))
        
        # XPOS
        fields.append(token.get('xpos', '_'))
        
        # FEATS
        feats = token.get('feats', {})
        if isinstance(feats, dict) and feats:
            feat_str = '|'.join(f"{k}={v}" for k, v in sorted(feats.items()))
            fields.append(feat_str)
        else:
            fields.append('_')
        
        # HEAD
        head = token.get('head', 0)
        fields.append(str(head))
        
        # DEPREL
        fields.append(token.get('deprel', '_'))
        
        # DEPS
        deps = token.get('deps')
        fields.append(deps if deps else '_')
        
        # MISC
        misc = token.get('misc', {})
        if isinstance(misc, dict) and misc:
            misc_str = '|'.join(f"{k}={v}" for k, v in sorted(misc.items()))
            fields.append(misc_str)
        else:
            fields.append('_')
        
        return '\t'.join(fields)
    
    @staticmethod
    def validate(conllu_text: str) -> Tuple[bool, List[str]]:
        """
        Validate CoNLL-U format.
        
        Args:
            conllu_text: String to validate
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
            
        Example:
            >>> is_valid, errors = CoNLLUParser.validate(text)
            >>> if not is_valid:
            ...     print(errors)
        """
        errors = []
        line_num = 0
        token_ids = set()
        sentence_token_ids = set()
        
        for line in conllu_text.strip().split('\n'):
            line_num += 1
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                # Reset sentence token IDs on empty line
                if not line:
                    sentence_token_ids = set()
                continue
            
            # Check field count
            fields = line.split('\t')
            if len(fields) != 10:
                errors.append(f"Line {line_num}: Expected 10 fields, got {len(fields)}")
                continue
            
            # Validate ID field
            id_field = fields[0]
            
            # Skip multi-word tokens and empty nodes for validation
            if '-' in id_field or '.' in id_field:
                continue
            
            try:
                token_id = int(id_field)
                if token_id in sentence_token_ids:
                    errors.append(f"Line {line_num}: Duplicate token ID {token_id} in sentence")
                sentence_token_ids.add(token_id)
                token_ids.add(token_id)
            except ValueError:
                errors.append(f"Line {line_num}: Invalid token ID '{id_field}'")
                continue
            
            # Validate HEAD field
            head_field = fields[6]
            if head_field != '_':
                try:
                    head = int(head_field)
                    if head < 0:
                        errors.append(f"Line {line_num}: HEAD must be non-negative, got {head}")
                except ValueError:
                    errors.append(f"Line {line_num}: Invalid HEAD value '{head_field}'")
            
            # Validate FEATS field format
            feats_field = fields[5]
            if feats_field != '_':
                if not re.match(r'^[A-Za-z]+=.+(\|[A-Za-z]+=.+)*$', feats_field):
                    errors.append(f"Line {line_num}: Invalid FEATS format '{feats_field}'")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def extract_sentences(conllu_text: str) -> List[List[Dict]]:
        """
        Split multi-sentence CoNLL-U into separate sentence token lists.
        
        Args:
            conllu_text: CoNLL-U formatted text (possibly multiple sentences)
            
        Returns:
            List of sentence token lists
            
        Example:
            >>> sentences = CoNLLUParser.extract_sentences(text)
            >>> len(sentences)
            3
            >>> len(sentences[0])  # tokens in first sentence
            5
        """
        tokens = CoNLLUParser.parse(conllu_text)
        
        if not tokens:
            return []
        
        # Group tokens by sentence_id
        sentences = []
        current_sentence = []
        current_sentence_id = tokens[0].get('sentence_id', 0)
        
        for token in tokens:
            sentence_id = token.get('sentence_id', 0)
            
            if sentence_id != current_sentence_id:
                if current_sentence:
                    sentences.append(current_sentence)
                current_sentence = []
                current_sentence_id = sentence_id
            
            current_sentence.append(token)
        
        # Add last sentence
        if current_sentence:
            sentences.append(current_sentence)
        
        return sentences
    
    @staticmethod
    def get_sentence_text(tokens: List[Dict]) -> str:
        """
        Reconstruct sentence text from tokens.
        
        Args:
            tokens: List of token dictionaries for a single sentence
            
        Returns:
            Reconstructed sentence text
        """
        if not tokens:
            return ""
        
        # Check if sentence_text is already stored
        if 'sentence_text' in tokens[0]:
            return tokens[0]['sentence_text']
        
        # Reconstruct from forms
        words = []
        for token in tokens:
            form = token.get('form', '')
            misc = token.get('misc', {})
            
            # Check for SpaceAfter=No
            if misc.get('SpaceAfter') == 'No':
                if words:
                    words[-1] += form
                else:
                    words.append(form)
            else:
                words.append(form)
        
        return ' '.join(words)


# Utility functions for common operations

def find_root(tokens: List[Dict]) -> Optional[Dict]:
    """Find the root token (head=0) in a sentence."""
    for token in tokens:
        if token.get('head') == 0:
            return token
    return None


def find_dependents(tokens: List[Dict], head_id: int) -> List[Dict]:
    """Find all tokens that depend on the given head."""
    return [t for t in tokens if t.get('head') == head_id]


def build_tree(tokens: List[Dict]) -> Dict:
    """
    Build a tree structure from flat token list.
    
    Returns:
        Tree structure where each node has 'token' and 'children' keys
    """
    root = find_root(tokens)
    if not root:
        return {}
    
    def build_node(token):
        children = find_dependents(tokens, token['id'])
        return {
            'token': token,
            'children': [build_node(child) for child in children]
        }
    
    return build_node(root)
