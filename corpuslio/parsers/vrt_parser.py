"""
VRT (Vertical Text Format) Parser for Corpus Linguistics.

VRT is a standard format used in corpus linguistics, particularly by
Sketch Engine and corpus query systems. Format:

Structure:
- One token per line
- Tab-separated columns (word, POS, lemma, features...)
- XML-like tags for structural elements (<text>, <s>, <p>)
- Metadata in opening tags

Example:
    <text id="doc1" author="Ahmet Yılmaz" year="2024">
    <s>
    Türk	NOUN	türk	Case=Nom
    dili	NOUN	dil	Case=Nom|Number=Sing
    çok	ADV	çok	_
    zengindir	ADJ	zengin	Tense=Pres
    .	PUNCT	.	_
    </s>
    </text>

Usage:
    from corpuslio.parsers.vrt_parser import VRTParser
    
    parser = VRTParser()
    vrt_data = parser.parse_file('corpus.vrt')
    conllu_data = parser.vrt_to_conllu(vrt_data)
"""

import re
from typing import List, Dict, Any, Optional, Tuple


class VRTParser:
    """Parser for VRT (Vertical Text Format) corpus files."""
    
    def __init__(self):
        """Initialize VRT parser."""
        self.tag_pattern = re.compile(r'<(/?)(\w+)(.*?)>')
        self.attr_pattern = re.compile(r'(\w+)="([^"]*)"')
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a VRT file.
        
        Args:
            file_path: Path to VRT file
        
        Returns:
            dict: Parsed VRT structure with metadata and tokens
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return self.parse_string(f.read())
    
    def parse_string(self, vrt_string: str) -> Dict[str, Any]:
        """Parse VRT format string.
        
        Args:
            vrt_string: VRT formatted text
        
        Returns:
            dict: Parsed structure with documents, sentences, and tokens
        """
        lines = vrt_string.strip().split('\n')
        
        documents = []
        current_doc = None
        current_sentence = None
        tag_stack = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if it's a tag
            if line.startswith('<'):
                tag_match = self.tag_pattern.match(line)
                if tag_match:
                    is_closing, tag_name, attrs_str = tag_match.groups()
                    
                    if is_closing:
                        # Closing tag
                        if tag_stack and tag_stack[-1] == tag_name:
                            tag_stack.pop()
                            
                            if tag_name == 's':
                                current_sentence = None
                            elif tag_name == 'text':
                                if current_doc:
                                    documents.append(current_doc)
                                current_doc = None
                        else:
                            raise ValueError(
                                f"Line {line_num}: Mismatched closing tag </{tag_name}>"
                            )
                    else:
                        # Opening tag
                        tag_stack.append(tag_name)
                        attributes = self._parse_attributes(attrs_str)
                        
                        if tag_name == 'text':
                            current_doc = {
                                'metadata': attributes,
                                'sentences': []
                            }
                        elif tag_name == 's':
                            current_sentence = {
                                'metadata': attributes,
                                'tokens': []
                            }
                            if current_doc is not None:
                                current_doc['sentences'].append(current_sentence)
                        elif tag_name == 'p':
                            # Paragraph marker (optional handling)
                            pass
                continue
            
            # Parse token line
            if current_sentence is not None:
                token_data = self._parse_token_line(line, line_num)
                current_sentence['tokens'].append(token_data)
        
        # Check for unclosed tags
        if tag_stack:
            raise ValueError(f"Unclosed tags: {', '.join(tag_stack)}")
        
        # Add last document if exists
        if current_doc:
            documents.append(current_doc)
        
        return {
            'documents': documents,
            'total_documents': len(documents),
            'total_sentences': sum(len(doc['sentences']) for doc in documents),
            'total_tokens': sum(
                len(sent['tokens'])
                for doc in documents
                for sent in doc['sentences']
            )
        }
    
    def _parse_attributes(self, attrs_str: str) -> Dict[str, str]:
        """Parse XML-like attributes string.
        
        Args:
            attrs_str: Attribute string (e.g., 'id="1" author="Name"')
        
        Returns:
            dict: Attribute key-value pairs
        """
        attributes = {}
        for match in self.attr_pattern.finditer(attrs_str):
            key, value = match.groups()
            attributes[key] = value
        return attributes
    
    def _parse_token_line(self, line: str, line_num: int) -> Dict[str, str]:
        """Parse a token line.
        
        Format: word\tPOS\tlemma\tfeatures
        
        Args:
            line: Token line
            line_num: Line number (for error messages)
        
        Returns:
            dict: Token data
        """
        parts = line.split('\t')
        
        if len(parts) < 1:
            raise ValueError(f"Line {line_num}: Empty token line")
        
        token = {
            'form': parts[0],
            'upos': parts[1] if len(parts) > 1 else '_',
            'lemma': parts[2] if len(parts) > 2 else '_',
            'feats': parts[3] if len(parts) > 3 else '_',
        }
        
        # Additional columns (optional)
        if len(parts) > 4:
            token['extra'] = parts[4:]
        
        return token
    
    def vrt_to_conllu(self, vrt_data: Dict[str, Any]) -> str:
        """Convert VRT structure to CoNLL-U format.
        
        Args:
            vrt_data: Parsed VRT data
        
        Returns:
            str: CoNLL-U formatted string
        """
        conllu_lines = []
        
        for doc in vrt_data['documents']:
            # Add document metadata as comments
            if doc['metadata']:
                for key, value in doc['metadata'].items():
                    conllu_lines.append(f"# newdoc {key} = {value}")
            
            for sent_idx, sentence in enumerate(doc['sentences'], 1):
                # Add sentence metadata
                if sentence['metadata']:
                    for key, value in sentence['metadata'].items():
                        conllu_lines.append(f"# {key} = {value}")
                else:
                    conllu_lines.append(f"# sent_id = {sent_idx}")
                
                # Add tokens
                for token_idx, token in enumerate(sentence['tokens'], 1):
                    conllu_line = '\t'.join([
                        str(token_idx),  # ID
                        token['form'],  # FORM
                        token['lemma'],  # LEMMA
                        token['upos'],  # UPOS
                        '_',  # XPOS (not in VRT)
                        token['feats'],  # FEATS
                        '_',  # HEAD (not in VRT)
                        '_',  # DEPREL (not in VRT)
                        '_',  # DEPS
                        '_',  # MISC
                    ])
                    conllu_lines.append(conllu_line)
                
                # Blank line after sentence
                conllu_lines.append('')
        
        return '\n'.join(conllu_lines)
    
    def conllu_to_vrt(
        self,
        conllu_string: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Convert CoNLL-U format to VRT.
        
        Args:
            conllu_string: CoNLL-U formatted text
            metadata: Optional document metadata
        
        Returns:
            str: VRT formatted string
        """
        vrt_lines = []
        
        # Add document opening tag
        if metadata:
            attrs = ' '.join(f'{k}="{v}"' for k, v in metadata.items())
            vrt_lines.append(f'<text {attrs}>')
        else:
            vrt_lines.append('<text>')
        
        # Parse CoNLL-U
        sentences = conllu_string.strip().split('\n\n')
        
        for sent_str in sentences:
            if not sent_str.strip():
                continue
            
            lines = sent_str.strip().split('\n')
            
            # Start sentence tag
            vrt_lines.append('<s>')
            
            for line in lines:
                if line.startswith('#'):
                    # Skip comments
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 7:
                    # Extract VRT columns: FORM, UPOS, LEMMA, FEATS
                    form = parts[1]
                    lemma = parts[2]
                    upos = parts[3]
                    feats = parts[5]
                    
                    vrt_line = f"{form}\t{upos}\t{lemma}\t{feats}"
                    vrt_lines.append(vrt_line)
            
            # End sentence tag
            vrt_lines.append('</s>')
        
        # Close document tag
        vrt_lines.append('</text>')
        
        return '\n'.join(vrt_lines)
    
    def export_to_vrt(
        self,
        tokens: List[Dict[str, str]],
        metadata: Optional[Dict[str, str]] = None,
        output_file: Optional[str] = None
    ) -> str:
        """Export token list to VRT format.
        
        Args:
            tokens: List of token dictionaries
            metadata: Document metadata
            output_file: Optional output file path
        
        Returns:
            str: VRT formatted string
        """
        vrt_lines = []
        
        # Document opening tag
        if metadata:
            attrs = ' '.join(f'{k}="{v}"' for k, v in metadata.items())
            vrt_lines.append(f'<text {attrs}>')
        else:
            vrt_lines.append('<text>')
        
        # Tokens (grouped by sentence if possible)
        current_sentence = []
        
        for token in tokens:
            # Check for sentence boundary (simplified)
            is_sent_end = token.get('form', '') in ['.', '!', '?', '...']
            
            current_sentence.append(token)
            
            if is_sent_end:
                # Write sentence
                vrt_lines.append('<s>')
                for t in current_sentence:
                    vrt_line = '\t'.join([
                        t.get('form', '_'),
                        t.get('upos', '_'),
                        t.get('lemma', '_'),
                        t.get('feats', '_'),
                    ])
                    vrt_lines.append(vrt_line)
                vrt_lines.append('</s>')
                current_sentence = []
        
        # Remaining tokens
        if current_sentence:
            vrt_lines.append('<s>')
            for t in current_sentence:
                vrt_line = '\t'.join([
                    t.get('form', '_'),
                    t.get('upos', '_'),
                    t.get('lemma', '_'),
                    t.get('feats', '_'),
                ])
                vrt_lines.append(vrt_line)
            vrt_lines.append('</s>')
        
        # Close document
        vrt_lines.append('</text>')
        
        vrt_string = '\n'.join(vrt_lines)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(vrt_string)
        
        return vrt_string
    
    def validate_vrt(self, vrt_string: str) -> Tuple[bool, List[str]]:
        """Validate VRT format.
        
        Args:
            vrt_string: VRT formatted text
        
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Try to parse
            result = self.parse_string(vrt_string)
            
            # Check for common issues
            if result['total_documents'] == 0:
                errors.append("No documents found")
            
            if result['total_sentences'] == 0:
                errors.append("No sentences found")
            
            if result['total_tokens'] == 0:
                errors.append("No tokens found")
            
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")
        
        return (len(errors) == 0, errors)


def demo():
    """Demonstration of VRT parser."""
    sample_vrt = """<text id="doc1" author="Test Author" year="2024">
<s>
Türk	NOUN	türk	Case=Nom
dili	NOUN	dil	Case=Nom|Number=Sing
çok	ADV	çok	_
zengindir	ADJ	zengin	Tense=Pres
.	PUNCT	.	_
</s>
<s>
Bu	DET	bu	Case=Nom
platformu	NOUN	platform	Case=Acc
araştırmacılar	NOUN	araştırmacı	Case=Nom|Number=Plur
kullanıyor	VERB	kullan	Aspect=Prog|Tense=Pres
.	PUNCT	.	_
</s>
</text>"""
    
    parser = VRTParser()
    
    print("="*70)
    print("VRT Parser Demo")
    print("="*70)
    
    # Parse VRT
    print("\n1. Parsing VRT...")
    result = parser.parse_string(sample_vrt)
    print(f"   Documents: {result['total_documents']}")
    print(f"   Sentences: {result['total_sentences']}")
    print(f"   Tokens: {result['total_tokens']}")
    
    # Convert to CoNLL-U
    print("\n2. Converting to CoNLL-U...")
    conllu = parser.vrt_to_conllu(result)
    print(conllu[:200] + "...")
    
    # Validate
    print("\n3. Validating VRT...")
    is_valid, errors = parser.validate_vrt(sample_vrt)
    if is_valid:
        print("   ✅ Valid VRT format")
    else:
        print("   ❌ Errors:")
        for err in errors:
            print(f"      - {err}")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    demo()
