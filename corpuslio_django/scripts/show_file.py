import os
paths = ['documents/2026/02/fake_tr_1k_uKYs5eM.conllu', 'media/documents/2026/02/fake_tr_1k_uKYs5eM.conllu']
for p in paths:
    print('CHECK:', p, os.path.exists(p))
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            s = f.read(800)
            print('PREVIEW:\n', s[:800])
