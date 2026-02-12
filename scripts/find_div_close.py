from pathlib import Path
s=Path('corpuslio_django/templates/corpus/profile.html').read_text(encoding='utf-8')
lines=s.splitlines()
start=None
for i,l in enumerate(lines,1):
    if '🎯 Hesap Durumu' in l:
        start=i
        break
if not start:
    print('start not found')
    raise SystemExit
# find the <div class="card"> that contains it by searching upward
card_start=None
for j in range(start,0,-1):
    if '<div class="card"' in lines[j-1]:
        card_start=j
        break
if not card_start:
    print('card start not found')
    raise SystemExit
print('card header line',start,'card start line',card_start)
# now track divs from card_start-1
depth=0
for k in range(card_start, len(lines)+1):
    line=lines[k-1]
    # count occurrences of <div and </div>
    depth += line.count('<div')
    depth -= line.count('</div>')
    if depth==0:
        print('card closes at line',k)
        break
else:
    print('no closing found')
