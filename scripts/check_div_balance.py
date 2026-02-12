from pathlib import Path
import re
p = Path(r"c:\Users\user\OneDrive\Belgeler\GitHub\corpuslio\corpuslio_django\templates\corpus\profile.html")
text = p.read_text(encoding='utf-8')
clean = re.sub(r"\{\%.*?\%\}", "", text, flags=re.S)
clean = re.sub(r"\{\{.*?\}\}", "", clean, flags=re.S)
lines = clean.splitlines()
balance = 0
for i,l in enumerate(lines, start=1):
    opens = len(re.findall(r"<div(\s[^>]*)?>", l, flags=re.I))
    closes = len(re.findall(r"</div>", l, flags=re.I))
    balance += opens - closes
    if balance < 0:
        print(f"Negative balance at line {i}: balance={balance}; line={l.strip()}")
        break
else:
    print(f"No negative balance encountered. Final balance: {balance}")

# print areas around the first negative or problem region
for i,l in enumerate(lines, start=1):
    pass
