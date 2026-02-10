import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
for t in ('corpus_document','corpus_sentence','corpus_token','corpus_corpusmetadata','corpus_content','corpus_analysis'):
    try:
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = cur.fetchall()
        print('\nTable:', t)
        for c in cols:
            print(' ', c)
    except Exception as e:
        print('\nTable:', t, 'error:', e)
conn.close()
