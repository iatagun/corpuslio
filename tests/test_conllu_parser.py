"""
Test CoNLL-U Parser

Tests for parsing, serializing, and validating CoNLL-U format.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ocrchestra.parsers.conllu_parser import CoNLLUParser, find_root, find_dependents, build_tree


# Sample Turkish CoNLL-U data
SAMPLE_CONLLU = """# text = Bu bir test cümlesidir.
1	Bu	bu	DET	Det	_	4	det	_	_
2	bir	bir	DET	Det	_	4	det	_	_
3	test	test	NOUN	Noun	Case=Nom	4	nmod	_	_
4	cümlesidir	cümle	NOUN	Noun	Case=Nom|Polarity=Pos	0	root	_	SpaceAfter=No
5	.	.	PUNCT	Punc	_	4	punct	_	_

# text = İkinci cümle.
1	İkinci	ikinci	ADJ	Adj	_	2	amod	_	_
2	cümle	cümle	NOUN	Noun	Case=Nom	0	root	_	SpaceAfter=No
3	.	.	PUNCT	Punc	_	2	punct	_	_
"""


def test_parse():
    """Test parsing CoNLL-U text."""
    print("=" * 60)
    print("TEST 1: Parsing CoNLL-U")
    print("=" * 60)
    
    tokens = CoNLLUParser.parse(SAMPLE_CONLLU)
    
    print(f"✅ Parsed {len(tokens)} tokens")
    
    # Check first token
    assert len(tokens) == 8, f"Expected 8 tokens, got {len(tokens)}"
    
    first_token = tokens[0]
    assert first_token['form'] == 'Bu', f"Expected 'Bu', got {first_token['form']}"
    assert first_token['lemma'] == 'bu', f"Expected 'bu', got {first_token['lemma']}"
    assert first_token['upos'] == 'DET', f"Expected 'DET', got {first_token['upos']}"
    assert first_token['head'] == 4, f"Expected head=4, got {first_token['head']}"
    assert first_token['deprel'] == 'det', f"Expected 'det', got {first_token['deprel']}"
    assert first_token['sentence_id'] == 0, f"Expected sentence_id=0, got {first_token['sentence_id']}"
    
    print(f"   First token: {first_token['form']} (lemma: {first_token['lemma']}, POS: {first_token['upos']})")
    print(f"   Head: {first_token['head']}, Deprel: {first_token['deprel']}")
    
    # Check token with features
    token_with_feats = tokens[3]
    assert 'feats' in token_with_feats, "Missing 'feats' field"
    assert token_with_feats['feats']['Case'] == 'Nom', "Wrong Case feature"
    assert token_with_feats['feats']['Polarity'] == 'Pos', "Wrong Polarity feature"
    print(f"   Token with features: {token_with_feats['form']}")
    print(f"   Features: {token_with_feats['feats']}")
    
    # Check sentence boundaries
    sentence_ids = set(t['sentence_id'] for t in tokens)
    assert len(sentence_ids) == 2, f"Expected 2 sentences, got {len(sentence_ids)}"
    print(f"✅ Sentence boundaries detected: {len(sentence_ids)} sentences")
    
    print()


def test_serialize():
    """Test serializing tokens to CoNLL-U."""
    print("=" * 60)
    print("TEST 2: Serializing to CoNLL-U")
    print("=" * 60)
    
    # Parse then serialize
    tokens = CoNLLUParser.parse(SAMPLE_CONLLU)
    conllu_output = CoNLLUParser.serialize(tokens, include_metadata=True)
    
    print(f"✅ Serialized {len(tokens)} tokens")
    print("\nOutput (first 300 chars):")
    print(conllu_output[:300])
    
    # Check output contains key elements
    assert '# text = Bu bir test cümlesidir.' in conllu_output
    assert 'Bu\tbu\tDET' in conllu_output
    assert 'Case=Nom|Polarity=Pos' in conllu_output
    
    # Parse serialized output to verify round-trip
    reparsed = CoNLLUParser.parse(conllu_output)
    assert len(reparsed) == len(tokens), "Round-trip parsing failed"
    
    print("✅ Round-trip parsing successful")
    print()


def test_validate():
    """Test validation."""
    print("=" * 60)
    print("TEST 3: Validation")
    print("=" * 60)
    
    # Valid CoNLL-U
    is_valid, errors = CoNLLUParser.validate(SAMPLE_CONLLU)
    assert is_valid, f"Valid CoNLL-U marked as invalid: {errors}"
    print("✅ Valid CoNLL-U passed validation")
    
    # Invalid CoNLL-U (wrong number of fields)
    invalid_conllu = "1\tBu\tbu\tDET\tDet\t_\t4\tdet"  # Only 8 fields instead of 10
    is_valid, errors = CoNLLUParser.validate(invalid_conllu)
    assert not is_valid, "Invalid CoNLL-U marked as valid"
    assert len(errors) > 0, "No errors reported for invalid CoNLL-U"
    print(f"✅ Invalid CoNLL-U detected: {errors[0]}")
    
    # Invalid HEAD value
    invalid_head = "1\tBu\tbu\tDET\tDet\t_\t-5\tdet\t_\t_"
    is_valid, errors = CoNLLUParser.validate(invalid_head)
    assert not is_valid, "Invalid HEAD not detected"
    print(f"✅ Invalid HEAD detected: {errors[0]}")
    
    print()


def test_extract_sentences():
    """Test sentence extraction."""
    print("=" * 60)
    print("TEST 4: Sentence Extraction")
    print("=" * 60)
    
    sentences = CoNLLUParser.extract_sentences(SAMPLE_CONLLU)
    
    assert len(sentences) == 2, f"Expected 2 sentences, got {len(sentences)}"
    print(f"✅ Extracted {len(sentences)} sentences")
    
    # First sentence should have 5 tokens
    assert len(sentences[0]) == 5, f"Expected 5 tokens in first sentence, got {len(sentences[0])}"
    print(f"   Sentence 1: {len(sentences[0])} tokens")
    
    # Second sentence should have 3 tokens
    assert len(sentences[1]) == 3, f"Expected 3 tokens in second sentence, got {len(sentences[1])}"
    print(f"   Sentence 2: {len(sentences[1])} tokens")
    
    # Check sentence text reconstruction
    sent1_text = CoNLLUParser.get_sentence_text(sentences[0])
    print(f"   Sentence 1 text: '{sent1_text}'")
    assert 'Bu bir test cümlesidir.' in sent1_text or 'Bu bir test cümlesidir' in sent1_text
    
    print()


def test_utility_functions():
    """Test utility functions."""
    print("=" * 60)
    print("TEST 5: Utility Functions")
    print("=" * 60)
    
    tokens = CoNLLUParser.parse(SAMPLE_CONLLU)
    
    # Get first sentence tokens
    first_sentence = [t for t in tokens if t['sentence_id'] == 0]
    
    # Find root
    root = find_root(first_sentence)
    assert root is not None, "Root not found"
    assert root['deprel'] == 'root', f"Expected root deprel, got {root['deprel']}"
    assert root['form'] == 'cümlesidir', f"Wrong root form: {root['form']}"
    print(f"✅ Root found: {root['form']} (ID: {root['id']})")
    
    # Find dependents of root
    dependents = find_dependents(first_sentence, root['id'])
    print(f"✅ Root has {len(dependents)} dependents:")
    for dep in dependents:
        print(f"   - {dep['form']} ({dep['deprel']})")
    
    # Build tree
    tree = build_tree(first_sentence)
    assert 'token' in tree, "Tree missing 'token' key"
    assert 'children' in tree, "Tree missing 'children' key"
    assert tree['token']['form'] == 'cümlesidir', "Wrong root in tree"
    assert len(tree['children']) == len(dependents), "Wrong number of children in tree"
    print(f"✅ Tree built: root={tree['token']['form']}, children={len(tree['children'])}")
    
    print()


def test_features_parsing():
    """Test morphological features parsing."""
    print("=" * 60)
    print("TEST 6: Features Parsing")
    print("=" * 60)
    
    # Create token with multiple features
    conllu_with_features = """1	kelime	kelime	NOUN	Noun	Case=Acc|Number=Sing|Person=3	0	root	_	_"""
    
    tokens = CoNLLUParser.parse(conllu_with_features)
    token = tokens[0]
    
    assert token['feats']['Case'] == 'Acc', "Case feature not parsed correctly"
    assert token['feats']['Number'] == 'Sing', "Number feature not parsed correctly"
    assert token['feats']['Person'] == '3', "Person feature not parsed correctly"
    
    print(f"✅ Features parsed correctly: {token['feats']}")
    
    # Test serialization preserves features
    serialized = CoNLLUParser.serialize(tokens, include_metadata=False)
    assert 'Case=Acc' in serialized
    assert 'Number=Sing' in serialized
    assert 'Person=3' in serialized
    
    print("✅ Features preserved in serialization")
    print()


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🚀 STARTING CoNLL-U PARSER TESTS")
    print("=" * 60)
    print()
    
    try:
        test_parse()
        test_serialize()
        test_validate()
        test_extract_sentences()
        test_utility_functions()
        test_features_parsing()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nCoNLL-U Parser is ready for production.")
        return True
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
