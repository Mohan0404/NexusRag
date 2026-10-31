import re

with open(r"D:\Academic-Projects\RAG\NexusRag\docs\interview\GENWORX_RAG_INTERVIEW_PREPARATION.md", encoding="utf-8", errors="ignore") as f:
    text = f.read()

m = re.search(r'## 23\..*?(?=## 24\.)', text, re.DOTALL)
if m:
    sec23 = m.group(0)
    cats = re.findall(r'### (Category [A-Z]:.*?)\n', sec23)
    print(f"Categories found: {len(cats)}")
    for c in cats:
        print(" ", c)
    
    questions = re.findall(r'#### (Q[0-9]+):\s*(.*?)\n>\s*\*\*Answer\*\*:\s*(.*?)(?=\n####|\n###|\Z)', sec23, re.DOTALL)
    print(f"Questions parsed: {len(questions)}")
    for q in questions[:5]:
        qid, qtext, qans = q
        print(f"  {qid}: {qtext[:50]}... -> Ans: {qans[:60]}...")
