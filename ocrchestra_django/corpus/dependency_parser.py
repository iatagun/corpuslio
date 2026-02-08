"""
CoNLL-U Dependency Parser Integration.

This module provides integration with Stanza for Turkish dependency parsing.
It handles automatic installation checks and provides a simple API for parsing.

Installation:
    pip install stanza
    python -c "import stanza; stanza.download('tr')"

Usage:
    from corpus.dependency_parser import DependencyParser
    
    parser = DependencyParser()
    if parser.is_available():
        conllu_str = parser.parse("Türk dili çok zengindir.")
"""

import sys
import os


class DependencyParser:
    """Wrapper for Stanza dependency parsing."""
    
    def __init__(self):
        """Initialize parser and check availability."""
        self._nlp = None
        self._available = None
    
    def is_available(self):
        """Check if Stanza is installed and Turkish model is downloaded.
        
        Returns:
            bool: True if parser is ready to use
        """
        if self._available is not None:
            return self._available
        
        try:
            import stanza
            
            # Try to initialize pipeline
            try:
                # Check if Turkish model exists
                import stanza.resources.common as common
                model_dir = common.DEFAULT_MODEL_DIR
                tr_model_path = os.path.join(model_dir, 'tr')
                
                if not os.path.exists(tr_model_path):
                    print("⚠️  Stanza Turkish model not found")
                    print("    Download: python -c \"import stanza; stanza.download('tr')\"")
                    self._available = False
                    return False
                
                self._available = True
                return True
                
            except Exception as e:
                print(f"⚠️  Stanza initialization error: {e}")
                self._available = False
                return False
                
        except ImportError:
            print("⚠️  Stanza not installed")
            print("    Install: pip install stanza")
            self._available = False
            return False
    
    def get_pipeline(self):
        """Get or initialize Stanza pipeline.
        
        Returns:
            stanza.Pipeline or None: Pipeline if available
        """
        if not self.is_available():
            return None
        
        if self._nlp is None:
            try:
                import stanza
                
                # Initialize with minimal logging
                self._nlp = stanza.Pipeline(
                    'tr',
                    processors='tokenize,pos,lemma,depparse',
                    verbose=False,
                    use_gpu=False  # CPU only for compatibility
                )
                
                print("✅ Stanza pipeline initialized")
                
            except Exception as e:
                print(f"❌ Failed to initialize Stanza pipeline: {e}")
                return None
        
        return self._nlp
    
    def parse(self, text):
        """Parse text and return CoNLL-U format.
        
        Args:
            text (str): Text to parse
        
        Returns:
            str or None: CoNLL-U formatted string, or None if parsing fails
        """
        nlp = self.get_pipeline()
        if nlp is None:
            return None
        
        try:
            doc = nlp(text)
            conllu_str = doc.to_conllu()
            return conllu_str
            
        except Exception as e:
            print(f"❌ Parsing error: {e}")
            return None
    
    @staticmethod
    def get_installation_guide():
        """Get installation instructions.
        
        Returns:
            str: Multi-line installation guide
        """
        return """
╔═══════════════════════════════════════════════════════════════════╗
║  CoNLL-U Dependency Parser - Installation Guide                  ║
╚═══════════════════════════════════════════════════════════════════╝

📦 Install Stanza:
   pip install stanza

📥 Download Turkish model:
   python -c "import stanza; stanza.download('tr')"

🔍 Verify installation:
   python -c "import stanza; print(stanza.__version__)"

💡 Usage in Django:
   from corpus.dependency_parser import DependencyParser
   
   parser = DependencyParser()
   if parser.is_available():
       conllu = parser.parse("Türk dili çok zengindir.")
       # Save to Analysis.conllu_data

📚 More info:
   https://stanfordnlp.github.io/stanza/
"""


# Singleton instance
_parser_instance = None


def get_parser():
    """Get singleton parser instance.
    
    Returns:
        DependencyParser: Shared parser instance
    """
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = DependencyParser()
    return _parser_instance
