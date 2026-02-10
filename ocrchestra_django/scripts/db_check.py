import sqlite3

def main():
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT id, filename, processed FROM corpus_document ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    print('Recent documents:')
    for r in rows:
        print(r)
    print('\nToken counts per document (recent list):')
    for r in rows:
        doc_id = r[0]
        cur.execute('SELECT COUNT(*) FROM corpus_token WHERE document_id=?', (doc_id,))
        count = cur.fetchone()[0]
        print(f'doc {doc_id}: {count} tokens')
    conn.close()

if __name__ == '__main__':
    main()
