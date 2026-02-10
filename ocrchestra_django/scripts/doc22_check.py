import sqlite3, json

doc_id = 22
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

print('Document ID:', doc_id)
cur.execute('SELECT id, filename, processed, token_count FROM corpus_document WHERE id=?', (doc_id,))
doc = cur.fetchone()
print('Document row:', doc)

cur.execute('SELECT COUNT(*) FROM corpus_sentence WHERE document_id=?', (doc_id,))
sent_count = cur.fetchone()[0]
print('Sentence count:', sent_count)

cur.execute('SELECT id, token_count, text FROM corpus_sentence WHERE document_id=? LIMIT 5', (doc_id,))
sents = cur.fetchall()
print('\nSample sentences (up to 5):')
for s in sents:
    sid, tokc, txt = s
    print(f'  sentence_id={sid} token_count={tokc} text_len={len(txt) if txt else 0}')
    if txt:
        print('    text_preview:', repr(txt[:120]))

cur.execute('SELECT COUNT(*) FROM corpus_token WHERE document_id=?', (doc_id,))
tok_count = cur.fetchone()[0]
print('\nToken count table:', tok_count)

cur.execute('SELECT id, form, lemma, upos FROM corpus_token WHERE document_id=? ORDER BY id LIMIT 10', (doc_id,))
tokens = cur.fetchall()
print('\nSample tokens (up to 10):')
for t in tokens:
    print(' ', t)

# Content
cur.execute('SELECT cleaned_text, raw_text FROM corpus_content WHERE document_id=?', (doc_id,))
row = cur.fetchone()
if row:
    cleaned, raw = row
    print('\nContent cleaned_text length:', len(cleaned) if cleaned else 0)
    print('Content raw_text length:', len(raw) if raw else 0)
else:
    print('\nNo content row')

# Analysis
cur.execute('SELECT data FROM corpus_analysis WHERE document_id=?', (doc_id,))
row = cur.fetchone()
if row and row[0]:
    try:
        data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        print('\nAnalysis data type:', type(data), 'len:', len(data) if isinstance(data, list) else 'N/A')
        if isinstance(data, list) and data:
            print('Sample analysis items:', json.dumps(data[:5], ensure_ascii=False))
    except Exception as e:
        print('\nAnalysis parsing error:', e)
else:
    print('\nNo analysis data or empty')

conn.close()
