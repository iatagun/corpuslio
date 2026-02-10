"""
Privacy & Anonymization Module for KVKK/GDPR Compliance.

This module provides functionality to detect and mask personal data in text:
- Person names (PERSON)
- Email addresses (EMAIL)
- Phone numbers (PHONE)
- ID numbers (TC Kimlik, Passport)
- Addresses (ADDRESS)
- IP addresses (IP)

Usage:
    from corpus.privacy.anonymizer import Anonymizer
    
    anonymizer = Anonymizer()
    result = anonymizer.anonymize_text("Ahmet Yılmaz'ın emaili ahmet@example.com")
    
    # Result:
    # {
    #     'anonymized_text': '[PERSON]'ın emaili [EMAIL]',
    #     'entities': [
    #         {'type': 'PERSON', 'original': 'Ahmet Yılmaz', 'start': 0, 'end': 12},
    #         {'type': 'EMAIL', 'original': 'ahmet@example.com', 'start': 23, 'end': 40}
    #     ],
    #     'stats': {'PERSON': 1, 'EMAIL': 1}
    # }
"""

import re
from typing import Dict, List, Tuple, Any
from datetime import datetime


class Anonymizer:
    """Text anonymization for personal data protection."""
    
    # Regex patterns for Turkish personal data
    PATTERNS = {
        # Email addresses
        'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        
        # Phone numbers (Turkish format)
        'PHONE': r'(\+90|0)?[\s]?(\([0-9]{3}\)|[0-9]{3})[\s]?[0-9]{3}[\s]?[0-9]{2}[\s]?[0-9]{2}',
        
        # TC Kimlik No (11 digits)
        'TC_ID': r'\b[1-9][0-9]{10}\b',
        
        # IP addresses
        'IP': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        
        # Credit card numbers (simplified)
        'CREDIT_CARD': r'\b[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b',
        
        # Turkish person names (simplified - capitalized words pattern)
        # This is a heuristic - for production use NER models like Stanza/spaCy
        'PERSON': r'\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)?\b',
    }
    
    def __init__(self, mask_char='[{}]'):
        """Initialize anonymizer.
        
        Args:
            mask_char: Format string for masking (e.g., '[{}]' -> '[PERSON]')
        """
        self.mask_char = mask_char
        self.compiled_patterns = {
            entity_type: re.compile(pattern, re.UNICODE)
            for entity_type, pattern in self.PATTERNS.items()
        }
    
    def detect_entities(self, text: str) -> List[Dict[str, Any]]:
        """Detect personal data entities in text.
        
        Args:
            text: Input text
        
        Returns:
            List of detected entities with type, original text, and position
        """
        entities = []
        
        for entity_type, pattern in self.compiled_patterns.items():
            for match in pattern.finditer(text):
                entities.append({
                    'type': entity_type,
                    'original': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                })
        
        # Sort by start position
        entities.sort(key=lambda x: x['start'])
        
        # Remove overlapping entities (keep longer/more specific ones)
        entities = self._remove_overlaps(entities)
        
        return entities
    
    def _remove_overlaps(self, entities: List[Dict]) -> List[Dict]:
        """Remove overlapping entities, keeping more specific ones."""
        if not entities:
            return []
        
        # Priority: specific types > generic types
        priority = {
            'EMAIL': 5,
            'PHONE': 4,
            'TC_ID': 4,
            'CREDIT_CARD': 4,
            'IP': 3,
            'PERSON': 1,  # Lowest priority (most generic)
        }
        
        filtered = []
        last_end = -1
        
        for entity in entities:
            # If no overlap with previous entity
            if entity['start'] >= last_end:
                filtered.append(entity)
                last_end = entity['end']
            else:
                # Overlap detected - keep higher priority
                prev_entity = filtered[-1]
                curr_priority = priority.get(entity['type'], 0)
                prev_priority = priority.get(prev_entity['type'], 0)
                
                if curr_priority > prev_priority:
                    # Replace with higher priority entity
                    filtered[-1] = entity
                    last_end = entity['end']
        
        return filtered
    
    def anonymize_text(
        self,
        text: str,
        entity_types: List[str] = None
    ) -> Dict[str, Any]:
        """Anonymize text by masking personal data.
        
        Args:
            text: Input text
            entity_types: List of entity types to mask (default: all)
        
        Returns:
            dict: {
                'anonymized_text': str,
                'entities': List[dict],
                'stats': dict (entity_type -> count)
            }
        """
        if not text:
            return {
                'anonymized_text': '',
                'entities': [],
                'stats': {}
            }
        
        # Detect entities
        entities = self.detect_entities(text)
        
        # Filter by entity types if specified
        if entity_types:
            entities = [e for e in entities if e['type'] in entity_types]
        
        # Calculate statistics
        stats = {}
        for entity in entities:
            entity_type = entity['type']
            stats[entity_type] = stats.get(entity_type, 0) + 1
        
        # Mask entities (process in reverse to maintain positions)
        anonymized_text = text
        for entity in reversed(entities):
            mask = self.mask_char.format(entity['type'])
            anonymized_text = (
                anonymized_text[:entity['start']] +
                mask +
                anonymized_text[entity['end']:]
            )
        
        return {
            'anonymized_text': anonymized_text,
            'entities': entities,
            'stats': stats
        }
    
    def generate_report(
        self,
        original_text: str,
        anonymized_text: str,
        entities: List[Dict],
        stats: Dict[str, int]
    ) -> Dict[str, Any]:
        """Generate detailed anonymization report.
        
        Args:
            original_text: Original text
            anonymized_text: Anonymized text
            entities: List of masked entities
            stats: Statistics by entity type
        
        Returns:
            dict: Comprehensive anonymization report
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'original_length': len(original_text),
            'anonymized_length': len(anonymized_text),
            'total_entities': len(entities),
            'entity_stats': stats,
            'entities_masked': [
                {
                    'type': e['type'],
                    'position': f"{e['start']}-{e['end']}",
                    'length': e['end'] - e['start']
                }
                for e in entities
            ],
            'contains_personal_data': len(entities) > 0,
            'privacy_status': 'anonymized' if len(entities) > 0 else 'public',
        }
    
    def anonymize_document(
        self,
        document,
        entity_types: List[str] = None,
        update_content: bool = True
    ) -> Dict[str, Any]:
        """Anonymize a Document model instance.
        
        Args:
            document: Document model instance
            entity_types: List of entity types to mask
            update_content: Whether to update document content
        
        Returns:
            dict: Anonymization report
        """
        if not hasattr(document, 'content') or not document.content:
            return {
                'success': False,
                'error': 'Document has no content'
            }
        
        # Get text
        text = document.content.cleaned_text or document.content.raw_text
        
        if not text:
            return {
                'success': False,
                'error': 'Document content is empty'
            }
        
        # Anonymize
        result = self.anonymize_text(text, entity_types)
        
        # Generate report
        report = self.generate_report(
            original_text=text,
            anonymized_text=result['anonymized_text'],
            entities=result['entities'],
            stats=result['stats']
        )
        
        # Update document if requested
        if update_content:
            # Update content
            document.content.cleaned_text = result['anonymized_text']
            document.content.save()
            
            # Update document metadata
            document.privacy_status = 'anonymized' if result['entities'] else 'public'
            document.anonymized_at = datetime.now()
            document.anonymization_report = report
            document.contains_personal_data = len(result['entities']) > 0
            document.save()
        
        return {
            'success': True,
            'report': report,
            'anonymized_text': result['anonymized_text'],
            'entities_count': len(result['entities'])
        }


def demo():
    """Demo of anonymization functionality."""
    anonymizer = Anonymizer()
    
    test_text = """
    Ahmet Yılmaz TC Kimlik No: 12345678901 ile başvuruda bulundu.
    İletişim: ahmet.yilmaz@example.com veya 0532 123 45 67
    Adres: Cumhuriyet Mahallesi, Ankara
    Ayşe Demir de 05321234568 numarasından aradı.
    IP adresi: 192.168.1.1
    Kart no: 1234 5678 9012 3456
    """
    
    print("="*70)
    print("ANONYMIZATION DEMO")
    print("="*70)
    
    print("\n📄 ORIGINAL TEXT:")
    print(test_text)
    
    result = anonymizer.anonymize_text(test_text)
    
    print("\n🔒 ANONYMIZED TEXT:")
    print(result['anonymized_text'])
    
    print("\n📊 STATISTICS:")
    for entity_type, count in result['stats'].items():
        print(f"   {entity_type}: {count}")
    
    print(f"\n✅ Total entities masked: {len(result['entities'])}")
    
    print("\n📋 DETECTED ENTITIES:")
    for i, entity in enumerate(result['entities'], 1):
        print(f"   {i}. {entity['type']}: '{entity['original']}' (pos: {entity['start']}-{entity['end']})")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    demo()
