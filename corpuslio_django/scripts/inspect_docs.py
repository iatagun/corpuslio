import sqlite3, json

def main():
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT id, filename, processed, token_count FROM corpus_document ORDER BY id DESC LIMIT 20")
    docs = cur.fetchall()
    print('id | filename | processed | token_count | has_content | content_len | has_analysis | analysis_len | sample_analysis')
    for d in docs:
        doc_id, filename, processed, token_count = d
        # content
        cur.execute('SELECT cleaned_text FROM corpus_content WHERE document_id=?', (doc_id,))
        row = cur.fetchone()
        has_content = bool(row)
        content_len = len(row[0]) if row and row[0] else 0
        # analysis
        cur.execute('SELECT data FROM corpus_analysis WHERE document_id=?', (doc_id,))
        row2 = cur.fetchone()
        has_analysis = bool(row2)
        analysis_len = 0
        sample = ''
        if row2 and row2[0]:
            try:
                data = json.loads(row2[0]) if isinstance(row2[0], str) else row2[0]
                analysis_len = len(data) if isinstance(data, list) else 1
                if isinstance(data, list) and data:
                    sample = json.dumps(data[:3], ensure_ascii=False)
                else:
                    sample = str(data)[:200]
            except Exception as e:
                sample = f'parse_error:{e}'
        print(f"{doc_id} | {filename} | {processed} | {token_count} | {has_content} | {content_len} | {has_analysis} | {analysis_len} | {sample}")
    conn.close()

if __name__ == '__main__':
    main()
