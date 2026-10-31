import re

with open(r"D:\Academic-Projects\RAG\NexusRag\docs\interview\GENWORX_RAG_INTERVIEW_PREPARATION.md", encoding="utf-8", errors="ignore") as f:
    text = f.read()

matches = list(re.finditer(r'^##\s+([0-9]+)\.\s+(.*?)$', text, re.MULTILINE))
print(f"Total section matches: {len(matches)}")
for i in range(len(matches)):
    num = matches[i].group(1)
    title = matches[i].group(2)
    start = matches[i].start()
    end = matches[i+1].start() if i+1 < len(matches) else len(text)
    chunk = text[start:end]
    print(f"Sec {num:>2}: {title[:45]:<45} ({len(chunk):>6} chars)")
