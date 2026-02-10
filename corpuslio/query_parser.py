"""CQP-style query parser for corpus pattern matching.

Supports:
- [word="pattern"] - word matching
- [lemma="pattern"] - lemma matching
- [pos="TAG"] - POS tag matching
- [word="pattern" & pos="TAG"] - multiple conditions
- [pos="ADJ"] [pos="NOUN"] - sequence patterns
- Regex support in patterns
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TokenConstraint:
    """Represents constraints for a single token position."""
    word_pattern: Optional[str] = None
    lemma_pattern: Optional[str] = None
    pos_pattern: Optional[str] = None
    is_regex: bool = True  # By default, patterns are treated as regex
    case_sensitive: bool = False
    
    def matches(self, token: Dict[str, Any]) -> bool:
        """Check if a token matches all constraints.
        
        Args:
            token: Dictionary with 'word', 'lemma', 'pos' keys
            
        Returns:
            True if token matches all active constraints
        """
        # Word pattern matching
        if self.word_pattern:
            word = token.get('word', '')
            if not self._match_pattern(word, self.word_pattern):
                return False
        
        # Lemma pattern matching
        if self.lemma_pattern:
            lemma = token.get('lemma', '')
            if not self._match_pattern(lemma, self.lemma_pattern):
                return False
        
        # POS pattern matching
        if self.pos_pattern:
            pos = token.get('pos', '')
            if not self._match_pattern(pos, self.pos_pattern):
                return False
        
        return True
    
    def _match_pattern(self, value: str, pattern: str) -> bool:
        """Match a value against a pattern.
        
        Args:
            value: Token attribute value
            pattern: Pattern to match (regex or literal)
            
        Returns:
            True if value matches pattern
        """
        if not value:
            return False
        
        flags = 0 if self.case_sensitive else re.IGNORECASE
        
        if self.is_regex:
            # Regex matching
            try:
                return bool(re.search(pattern, value, flags))
            except re.error:
                # Invalid regex, fall back to literal matching
                if self.case_sensitive:
                    return pattern in value
                else:
                    return pattern.lower() in value.lower()
        else:
            # Literal matching
            if self.case_sensitive:
                return pattern == value
            else:
                return pattern.lower() == value.lower()


@dataclass
class QueryPattern:
    """Represents a complete query pattern (sequence of token constraints)."""
    constraints: List[TokenConstraint]
    
    def __len__(self):
        return len(self.constraints)


class CQPQueryParser:
    """Parser for CQP-style corpus query patterns.
    
    Supported syntax:
    - [word="test"] - exact word match
    - [lemma="go"] - lemma match
    - [pos="NOUN"] - POS tag match
    - [word="test.*"] - regex word match
    - [word="test" & pos="NOUN"] - multiple constraints
    - [pos="ADJ"] [pos="NOUN"] - sequence pattern
    
    Examples:
        >>> parser = CQPQueryParser()
        >>> pattern = parser.parse('[pos="ADJ"] [pos="NOUN"]')
        >>> print(len(pattern.constraints))  # 2
    """
    
    # Regex to match a single token pattern: [attribute="value" & ...]
    TOKEN_PATTERN = re.compile(
        r'\[([^\]]+)\]'
    )
    
    # Regex to match attribute="value" pairs
    ATTR_PATTERN = re.compile(
        r'(word|lemma|pos)\s*=\s*"([^"]+)"'
    )
    
    def __init__(self):
        """Initialize CQP query parser."""
        self.last_error = None
    
    def parse(self, query: str) -> Optional[QueryPattern]:
        """Parse a CQP-style query into a QueryPattern.
        
        Args:
            query: CQP-style query string
            
        Returns:
            QueryPattern object or None if parsing fails
            
        Examples:
            >>> parser = CQPQueryParser()
            >>> pattern = parser.parse('[word="test"]')
            >>> pattern = parser.parse('[pos="ADJ"] [pos="NOUN"]')
            >>> pattern = parser.parse('[word="run.*" & pos="VERB"]')
        """
        self.last_error = None
        
        if not query or not query.strip():
            self.last_error = "Empty query"
            return None
        
        # Find all token patterns
        token_matches = self.TOKEN_PATTERN.findall(query)
        
        if not token_matches:
            self.last_error = "No valid token patterns found. Use format: [attribute=\"value\"]"
            return None
        
        constraints = []
        
        for token_str in token_matches:
            constraint = self._parse_token_constraint(token_str)
            if constraint is None:
                # Error already set in _parse_token_constraint
                return None
            constraints.append(constraint)
        
        return QueryPattern(constraints=constraints)
    
    def _parse_token_constraint(self, token_str: str) -> Optional[TokenConstraint]:
        """Parse a single token constraint string.
        
        Args:
            token_str: Content between brackets, e.g., 'word="test" & pos="NOUN"'
            
        Returns:
            TokenConstraint object or None if invalid
        """
        # Find all attribute="value" pairs
        attr_matches = self.ATTR_PATTERN.findall(token_str)
        
        if not attr_matches:
            self.last_error = f"No valid attributes found in [{token_str}]"
            return None
        
        constraint = TokenConstraint()
        
        for attr, value in attr_matches:
            if attr == 'word':
                constraint.word_pattern = value
            elif attr == 'lemma':
                constraint.lemma_pattern = value
            elif attr == 'pos':
                constraint.pos_pattern = value
        
        return constraint
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validate a CQP query without parsing.
        
        Args:
            query: CQP-style query string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pattern = self.parse(query)
        if pattern is None:
            return False, self.last_error
        return True, None
    
    def get_query_info(self, query: str) -> Dict[str, Any]:
        """Get information about a parsed query.
        
        Args:
            query: CQP-style query string
            
        Returns:
            Dictionary with query information
        """
        pattern = self.parse(query)
        
        if pattern is None:
            return {
                'valid': False,
                'error': self.last_error,
                'token_count': 0,
                'attributes_used': []
            }
        
        attributes_used = set()
        for constraint in pattern.constraints:
            if constraint.word_pattern:
                attributes_used.add('word')
            if constraint.lemma_pattern:
                attributes_used.add('lemma')
            if constraint.pos_pattern:
                attributes_used.add('pos')
        
        return {
            'valid': True,
            'token_count': len(pattern.constraints),
            'attributes_used': sorted(attributes_used),
            'is_sequence': len(pattern.constraints) > 1
        }


class PatternMatcher:
    """Pattern matching engine for corpus queries.
    
    Matches QueryPattern objects against token sequences.
    """
    
    def __init__(self):
        """Initialize pattern matcher."""
        pass
    
    def find_matches(
        self,
        pattern: QueryPattern,
        tokens: List[Dict[str, Any]],
        context_size: int = 5
    ) -> List[Dict[str, Any]]:
        """Find all matches of pattern in token sequence.
        
        Args:
            pattern: QueryPattern to match
            tokens: List of token dictionaries
            context_size: Number of tokens before/after match for context
            
        Returns:
            List of match dictionaries with context
        """
        matches = []
        pattern_len = len(pattern.constraints)
        
        # Slide window over tokens
        for i in range(len(tokens) - pattern_len + 1):
            # Check if pattern matches starting at position i
            if self._matches_at_position(pattern, tokens, i):
                # Extract match with context
                match = self._extract_match(
                    tokens=tokens,
                    start_pos=i,
                    pattern_len=pattern_len,
                    context_size=context_size
                )
                matches.append(match)
        
        return matches
    
    def _matches_at_position(
        self,
        pattern: QueryPattern,
        tokens: List[Dict[str, Any]],
        start_pos: int
    ) -> bool:
        """Check if pattern matches starting at given position.
        
        Args:
            pattern: QueryPattern to match
            tokens: List of token dictionaries
            start_pos: Starting position in tokens
            
        Returns:
            True if pattern matches
        """
        for i, constraint in enumerate(pattern.constraints):
            token_pos = start_pos + i
            
            # Out of bounds
            if token_pos >= len(tokens):
                return False
            
            # Check if token matches constraint
            if not constraint.matches(tokens[token_pos]):
                return False
        
        return True
    
    def _extract_match(
        self,
        tokens: List[Dict[str, Any]],
        start_pos: int,
        pattern_len: int,
        context_size: int
    ) -> Dict[str, Any]:
        """Extract match with context.
        
        Args:
            tokens: Full token list
            start_pos: Match start position
            pattern_len: Length of matched pattern
            context_size: Context window size
            
        Returns:
            Match dictionary with left_context, match, right_context
        """
        # Calculate context boundaries
        left_start = max(0, start_pos - context_size)
        right_end = min(len(tokens), start_pos + pattern_len + context_size)
        
        # Extract contexts and match
        left_context = tokens[left_start:start_pos]
        match_tokens = tokens[start_pos:start_pos + pattern_len]
        right_context = tokens[start_pos + pattern_len:right_end]
        
        return {
            'position': start_pos,
            'left_context': left_context,
            'match': match_tokens,
            'right_context': right_context,
            'left_context_text': ' '.join(t.get('word', '') for t in left_context),
            'match_text': ' '.join(t.get('word', '') for t in match_tokens),
            'right_context_text': ' '.join(t.get('word', '') for t in right_context)
        }


# Convenience functions

def parse_cqp_query(query: str) -> Optional[QueryPattern]:
    """Parse a CQP query string.
    
    Args:
        query: CQP-style query string
        
    Returns:
        QueryPattern or None
    """
    parser = CQPQueryParser()
    return parser.parse(query)


def search_pattern(
    query: str,
    tokens: List[Dict[str, Any]],
    context_size: int = 5
) -> List[Dict[str, Any]]:
    """Search for CQP pattern in token sequence.
    
    Args:
        query: CQP-style query string
        tokens: List of token dictionaries
        context_size: Context window size
        
    Returns:
        List of matches with context
    """
    pattern = parse_cqp_query(query)
    if pattern is None:
        return []
    
    matcher = PatternMatcher()
    return matcher.find_matches(pattern, tokens, context_size)
