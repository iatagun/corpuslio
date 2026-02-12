import re
from pathlib import Path
p=Path('corpuslio_django/templates/corpus/profile.html')
s=p.read_text(encoding='utf-8')
lines=s.splitlines()
stack=[]
pattern=re.compile(r"{%\s*(if|elif|else|endif)\b(.*?)%}")
for i,l in enumerate(lines, start=1):
    for m in pattern.finditer(l):
        tag=m.group(1)
        if tag=='if':
            stack.append((tag,i,m.group(0)))
        elif tag=='endif':
            if stack:
                stack.pop()
            else:
                print(f"Unmatched endif at line {i}")

if stack:
    print('Unclosed tags:')
    for t in stack:
        print(t)
else:
    print('All if/endif balanced')
