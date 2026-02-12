import re
import sys
from pathlib import Path

path = Path(r"c:\Users\user\OneDrive\Belgeler\GitHub\corpuslio\corpuslio_django\templates\corpus\profile.html")
text = path.read_text(encoding='utf-8')

# remove Django tags and expressions for simpler HTML parsing
clean = re.sub(r"\{\%.*?\%\}", "", text, flags=re.S)
clean = re.sub(r"\{\{.*?\}\}", "", clean, flags=re.S)

lines = clean.splitlines()
stack = []
errors = []
for i, line in enumerate(lines, start=1):
    # find all opening <div ...> and closing </div>
    for m in re.finditer(r"<div(\s[^>]*)?>", line, flags=re.I):
        stack.append((i, m.group(0)))
    for m in re.finditer(r"</div>", line, flags=re.I):
        if stack:
            stack.pop()
        else:
            # capture context: last few opens
            last_opens = stack[-5:]
            errors.append((i, 'extra closing </div>', list(last_opens)))

print('Total opening <div> remaining on stack:', len(stack))
if stack:
    print('Unclosed <div> (top 20):')
    for ln, tag in stack[-20:]:
        print(f'  line {ln}: {tag[:80]}')
if errors:
    print('\nExtra closing tags found:')
    for item in errors:
        ln, msg = item[0], item[1]
        ctx = item[2] if len(item) > 2 else []
        print(f'  line {ln}: {msg}; recent opens: {ctx}')
        # print surrounding lines for context
        start = max(1, ln-3)
        end = min(len(lines), ln+3)
        print(f'    context lines {start}-{end}:')
        for j in range(start, end+1):
            print(f'      {j}: {lines[j-1].strip()}')

# Also print surrounding lines for the last unclosed div to help locate
if stack:
    ln, _ = stack[-1]
    start = max(1, ln-8)
    end = min(len(lines), ln+8)
    print(f'\nContext around last unclosed opening <div> (line {ln}):')
    for j in range(start, end+1):
        print(f'{j:4}: {lines[j-1]}')

# Print where two-col-row opens
for i, line in enumerate(lines, start=1):
    if 'two-col-row' in line:
        print(f"\nFound 'two-col-row' at line {i} -> {line.strip()}")
        break


