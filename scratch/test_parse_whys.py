import re

with open(r"D:\Academic-Projects\RAG\NexusRag\docs\interview\GENWORX_RAG_INTERVIEW_PREPARATION.md", encoding="utf-8", errors="ignore") as f:
    text = f.read()

m = re.search(r'## 24\..*?(?=## 25\.)', text, re.DOTALL)
if m:
    sec24 = m.group(0)
    items = re.findall(r'### (Why .*?)\n(.*?)(?=\n###|\Z)', sec24, re.DOTALL)
    print(f"Why items parsed: {len(items)}")
    for title, body in items:
        print(f"  {title}")
