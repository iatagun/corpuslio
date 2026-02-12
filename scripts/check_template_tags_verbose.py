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
        print(f"Line {i}: found tag {m.group(0)!r}")
        if tag=='if':
            stack.append((tag,i,m.group(0)))
            print(f"  push if (line {i}), stack size {len(stack)}")
        elif tag=='endif':
            if stack:
                popped=stack.pop()
                print(f"  pop (matched if at line {popped[1]}), stack size {len(stack)}")
            else:
                print(f"  unmatched endif at line {i}")

print('FINAL STACK:')
for t in stack:
    print(t)
