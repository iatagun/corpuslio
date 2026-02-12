from pathlib import Path
lines=Path('corpuslio_django/templates/corpus/profile.html').read_text(encoding='utf-8').splitlines()
start=None
for i,l in enumerate(lines,1):
    if 'Quota Tracking Card' in l:
        for j in range(i, i+10):
            if '<div class="card"' in lines[j-1]:
                start=j
                break
        break
print('quota card start line',start)
depth=0
for k in range(start, len(lines)+1):
    depth += lines[k-1].count('<div')
    depth -= lines[k-1].count('</div>')
    if depth==0:
        print('quota card closes at',k)
        break
