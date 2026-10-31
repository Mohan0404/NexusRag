"""
Master Compilation Script for NexusRAG Project Defense Handbook.
Builds the complete HTML and generates the high-resolution PDF.
"""
import os
import sys
import re
import html
import json
import markdown_it
from playwright.sync_api import sync_playwright

DOCS_DIR = r"D:\Academic-Projects\RAG\docs\interview"
NEXUS_DIR = r"D:\Academic-Projects\RAG\NexusRag\docs\interview"
CSS_PATH = os.path.join(DOCS_DIR, "assets", "css", "handbook.css")
DIAGRAMS_DIR = os.path.join(DOCS_DIR, "assets", "diagrams")
MD_SOURCE = os.path.join(NEXUS_DIR, "GENWORX_RAG_INTERVIEW_PREPARATION.md")

md = markdown_it.MarkdownIt("gfm-like")

def render_md(text):
    return md.render(text)

def load_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def load_svg(name):
    path = os.path.join(DIAGRAMS_DIR, name)
    if os.path.exists(path):
        return load_file(path)
    return f"<!-- SVG {name} missing -->"

# Part divider builder
def build_part_divider(roman, title, quote, topics):
    topics_html = "".join([f"""
    <div class="part-topic-item">
      <h4>{t['title']}</h4>
      <p>{t['desc']}</p>
    </div>
    """ for t in topics])

    return f"""
    <div class="part-divider page-break" id="part-{roman.lower()}">
      <div class="part-num-badge">PART {roman}</div>
      <h1 class="part-title">{title}</h1>
      <div class="part-subtitle">"{quote}"</div>
      <div class="part-topics-grid">
        {topics_html}
      </div>
    </div>
    """

# Section header builder
def build_section_header(num_str, title, summary, sec_id):
    return f"""
    <div class="section-header" id="{sec_id}">
      <div class="section-num">{num_str}</div>
      <div class="section-meta">
        <h2 class="section-title">{title}</h2>
        <p class="section-summary">{summary}</p>
      </div>
    </div>
    """

# Diagram box builder
def build_diagram_box(fig_num, title, svg_name, what, how, why, interview_point):
    svg_content = load_svg(svg_name)
    return f"""
    <div class="diagram-box no-break" id="fig-{fig_num.lower()}">
      <div class="diagram-header">
        <div class="diagram-title">{title}</div>
        <div class="diagram-figure-num">FIGURE {fig_num}</div>
      </div>
      <div class="diagram-svg-wrapper">
        {svg_content}
      </div>
      <div class="diagram-explanation-grid">
        <div class="diagram-exp-item">
          <span class="exp-tag">WHAT YOU ARE LOOKING AT</span>
          <p>{what}</p>
        </div>
        <div class="diagram-exp-item">
          <span class="exp-tag">HOW DATA MOVES</span>
          <p>{how}</p>
        </div>
        <div class="diagram-exp-item">
          <span class="exp-tag">WHY IT IS DESIGNED THIS WAY</span>
          <p>{why}</p>
        </div>
        <div class="diagram-exp-item">
          <span class="exp-tag">KEY INTERVIEW POINT</span>
          <p>{interview_point}</p>
        </div>
      </div>
    </div>
    """

# Callout builder
def build_callout(callout_type, title, text):
    type_class = f"callout-{callout_type.lower()}"
    icons = {
        "info": "ℹ️",
        "warning": "⚠️",
        "security": "🔒",
        "tip": "💡",
        "scale": "📈",
        "limitation": "🚧",
        "decision": "⚙️",
        "source": "📋"
    }
    icon = icons.get(callout_type.lower(), "ℹ️")
    return f"""
    <div class="callout {type_class} no-break">
      <div class="callout-header"><span>{icon}</span> {title}</div>
      <p>{text}</p>
    </div>
    """

# Stat card builder
def build_stat_card(val, label, desc):
    return f"""
    <div class="stat-card">
      <div class="stat-val">{val}</div>
      <div class="stat-lbl">{label}</div>
      <div class="stat-desc">{desc}</div>
    </div>
    """

# Decision card builder
def build_decision_card(title, decision, rationale_list, tradeoff, alternative, when_to_change):
    rat_html = "".join([f"<li>{r}</li>" for r in rationale_list])
    return f"""
    <div class="decision-card no-break">
      <div class="decision-header">
        <div class="decision-title">⚙️ {title}</div>
        <span class="decision-badge">VERIFIED SELECTION</span>
      </div>
      <div class="decision-content">
        <p style="font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">Decision: {decision}</p>
        <ul>{rat_html}</ul>
      </div>
      <div class="decision-meta-row">
        <div class="decision-meta-item">
          <span class="key">Trade-off</span>
          <span class="val">{tradeoff}</span>
        </div>
        <div class="decision-meta-item">
          <span class="key">Alternative</span>
          <span class="val">{alternative}</span>
        </div>
        <div class="decision-meta-item">
          <span class="key">When to Change</span>
          <span class="val">{when_to_change}</span>
        </div>
      </div>
    </div>
    """

# Tradeoff card builder
def build_tradeoff_card(title, decision, benefit, cost, limitation, production):
    return f"""
    <div class="tradeoff-card no-break">
      <div class="tradeoff-title">⚖️ {title}</div>
      <p style="font-size: 8.5pt; color: var(--text-secondary); margin-bottom: 8px;"><strong>Core Decision:</strong> {decision}</p>
      <div class="tradeoff-grid">
        <div class="tradeoff-box benefit">
          <div class="box-lbl">Immediate Engineering Benefit</div>
          <p>{benefit}</p>
        </div>
        <div class="tradeoff-box cost">
          <div class="box-lbl">Architectural Cost / Compromise</div>
          <p>{cost}</p>
        </div>
        <div class="tradeoff-box limitation">
          <div class="box-lbl">Current System Limitation</div>
          <p>{limitation}</p>
        </div>
        <div class="tradeoff-box alternative">
          <div class="box-lbl">Scaled Production Solution</div>
          <p>{production}</p>
        </div>
      </div>
    </div>
    """

# Interview card builder
def build_interview_card(qid, difficulty, question, answer, why, tradeoff, limitation, at_scale):
    diff_classes = {
        "FOUNDATION": "badge-foundation",
        "INTERMEDIATE": "badge-intermediate",
        "ADVANCED": "badge-advanced",
        "SYSTEM DESIGN": "badge-system"
    }
    diff_class = diff_classes.get(difficulty, "badge-intermediate")
    icons = {
        "FOUNDATION": "🟢",
        "INTERMEDIATE": "🟡",
        "ADVANCED": "🔴",
        "SYSTEM DESIGN": "🟣"
    }
    icon = icons.get(difficulty, "🟡")

    return f"""
    <div class="interview-card no-break" id="{qid.lower()}">
      <div class="interview-top">
        <span class="interview-id">{qid}</span>
        <span class="difficulty-badge {diff_class}">{icon} {difficulty}</span>
      </div>
      <div class="interview-question">{question}</div>
      <div class="interview-answer">
        <strong>Verbal Answer:</strong> {answer}
      </div>
      <div class="interview-details-grid">
        <div class="interview-detail-item">
          <span class="lbl">Why Designed This Way</span>
          <span class="val">{why}</span>
        </div>
        <div class="interview-detail-item">
          <span class="lbl">Architectural Trade-Off</span>
          <span class="val">{tradeoff}</span>
        </div>
        <div class="interview-detail-item">
          <span class="lbl">Known Limitation</span>
          <span class="val">{limitation}</span>
        </div>
        <div class="interview-detail-item">
          <span class="lbl">At Production Scale</span>
          <span class="val">{at_scale}</span>
        </div>
      </div>
    </div>
    """

# Code card builder
def build_code_card(filepath, function_name, purpose, code_snippet, interview_q, why_answer):
    escaped_code = html.escape(code_snippet.strip())
    return f"""
    <div class="code-card no-break">
      <div class="code-header">
        <div class="code-file">📄 {filepath} &gt; {function_name}()</div>
        <div class="code-purpose">{purpose}</div>
      </div>
      <pre><code>{escaped_code}</code></pre>
      <div class="code-interviewer-note">
        <strong>Interviewer Question:</strong> "{interview_q}"<br/>
        <strong>Engineering Rationale:</strong> {why_answer}
      </div>
    </div>
    """

# User story card builder
def build_user_story_card(flow_id, title, actor, trigger, preconditions, technical_steps, result, failure_cases):
    steps_html = "".join([f"<li>{s}</li>" for s in technical_steps])
    return f"""
    <div class="user-story-card no-break">
      <div class="user-story-header">
        <span class="user-story-id">{flow_id}</span>
        <span class="user-story-actor">Actor: {actor}</span>
      </div>
      <div class="user-story-title">{title}</div>
      <p style="font-size: 8pt; color: var(--text-secondary); margin-bottom: 4px;"><strong>Trigger:</strong> {trigger}</p>
      <p style="font-size: 8pt; color: var(--text-secondary); margin-bottom: 4px;"><strong>Preconditions:</strong> {preconditions}</p>
      <div style="margin: 6px 0;">
        <strong style="font-size: 7.5pt; text-transform: uppercase; color: var(--primary);">Technical Flow:</strong>
        <ol style="padding-left: 18px; font-size: 8pt; color: var(--text-secondary); margin-top: 3px;">
          {steps_html}
        </ol>
      </div>
      <div class="user-story-body-grid">
        <div>
          <strong style="font-size: 7pt; text-transform: uppercase; color: var(--success-text);">Result:</strong>
          <p style="font-size: 7.5pt; color: var(--text-secondary); margin: 0;">{result}</p>
        </div>
        <div>
          <strong style="font-size: 7pt; text-transform: uppercase; color: var(--danger-text);">Failure Cases:</strong>
          <p style="font-size: 7.5pt; color: var(--text-secondary); margin: 0;">{failure_cases}</p>
        </div>
      </div>
    </div>
    """

def build_cover_page():
    abstract_svg = load_svg("diagram_cover_abstract.svg")
    return f"""
    <div class="cover-page" id="cover">
      <div class="cover-header">
        <div class="cover-badge">PROJECT DEFENSE HANDBOOK · SENIOR AI ENGINEERING</div>
        <div class="cover-meta-right">PHASES 1–15 VERIFIED · PRODUCTION-ALIGNED</div>
      </div>

      <div class="cover-hero">
        <h1 class="cover-title">NexusRAG <span>Handbook</span></h1>
        <div class="cover-subtitle">Genworx Knowledge Assistant</div>
        <p class="cover-tagline">
          An enterprise-grade, retrieval-augmented generation assistant designed for deterministic institutional knowledge recovery, verifiable page-level citation attribution, and sub-10ms cached query responses.
        </p>

        <div class="cover-tech-strip">
          <div class="tech-chip"><span class="tech-chip-dot"></span>React 18 SPA</div>
          <div class="tech-chip"><span class="tech-chip-dot"></span>FastAPI (Uvicorn ASGI)</div>
          <div class="tech-chip"><span class="tech-chip-dot"></span>LangChain Core</div>
          <div class="tech-chip"><span class="tech-chip-dot"></span>Google Gemini Embedding 2</div>
          <div class="tech-chip"><span class="tech-chip-dot"></span>ChromaDB (HNSW + SQLite)</div>
          <div class="tech-chip"><span class="tech-chip-dot"></span>Redis Distributed Cache</div>
          <div class="tech-chip"><span class="tech-chip-dot"></span>OpenRouter AI Gateway</div>
          <div class="tech-chip"><span class="tech-chip-dot"></span>Google Gemini 2.5 Flash</div>
        </div>

        <div class="cover-visual-container">
          {abstract_svg}
        </div>
      </div>

      <div class="cover-footer">
        <div class="cover-stat-box">
          <div class="val">184</div>
          <div class="lbl">Backend Tests</div>
        </div>
        <div class="cover-stat-box">
          <div class="val">52</div>
          <div class="lbl">Frontend Tests</div>
        </div>
        <div class="cover-stat-box">
          <div class="val">236</div>
          <div class="lbl">Total Tests (100% Pass)</div>
        </div>
        <div class="cover-stat-box">
          <div class="val">15</div>
          <div class="lbl">Engineering Phases</div>
        </div>
      </div>
    </div>
    """

def build_toc():
    return """
    <div class="toc-container page-break" id="table-of-contents">
      <h2 class="toc-title">Table of Contents</h2>
      <div class="toc-grid">
        <div class="toc-part-group">
          <div class="toc-part-header">PART I — PROJECT STORY &amp; MOTIVATION</div>
          <ul class="toc-list">
            <li><a href="#sec-01">01. Executive Overview &amp; Problem Solved</a> <span>p. 3</span></li>
            <li><a href="#sec-02">02. Implemented User Stories &amp; Flows A–S</a> <span>p. 5</span></li>
            <li><a href="#sec-03">03. Executive Pitches (30s, 2m, 5m Deep Dive)</a> <span>p. 8</span></li>
          </ul>
        </div>

        <div class="toc-part-group">
          <div class="toc-part-header">PART II — SYSTEM ARCHITECTURE</div>
          <ul class="toc-list">
            <li><a href="#sec-04">04. Architecture Overview &amp; Stat Cards</a> <span>p. 10</span></li>
            <li><a href="#sec-05">05. Master System Architecture (Figure A)</a> <span>p. 11</span></li>
            <li><a href="#sec-06">06. Low-Level Component Layout (Figure E)</a> <span>p. 13</span></li>
            <li><a href="#sec-07">07. End-to-End Request Lifecycle (Figure J)</a> <span>p. 15</span></li>
            <li><a href="#sec-08">08. Project File-by-File Breakdown</a> <span>p. 17</span></li>
          </ul>
        </div>

        <div class="toc-part-group">
          <div class="toc-part-header">PART III — DOCUMENT → KNOWLEDGE BASE</div>
          <ul class="toc-list">
            <li><a href="#sec-09">09. Ingestion Pipeline (Figure B)</a> <span>p. 20</span></li>
            <li><a href="#sec-10">10. Format Loaders (PDF, TXT, MD)</a> <span>p. 22</span></li>
            <li><a href="#sec-11">11. Text Sanitization &amp; Normalization</a> <span>p. 23</span></li>
            <li><a href="#sec-12">12. Recursive Chunking (800 / 100 char)</a> <span>p. 24</span></li>
            <li><a href="#sec-13">13. Metadata Tagging &amp; Document Isolation</a> <span>p. 25</span></li>
            <li><a href="#sec-14">14. Gemini Embedding 2 (768-Dim Dense)</a> <span>p. 26</span></li>
            <li><a href="#sec-15">15. ChromaDB Vector Store &amp; Persistence</a> <span>p. 28</span></li>
          </ul>
        </div>

        <div class="toc-part-group">
          <div class="toc-part-header">PART IV — QUESTION → ANSWER (RAG)</div>
          <ul class="toc-list">
            <li><a href="#sec-16">16. Query Execution &amp; Retrieval (Figure C)</a> <span>p. 30</span></li>
            <li><a href="#sec-17">17. Redis Distributed Query Cache (Figure D)</a> <span>p. 32</span></li>
            <li><a href="#sec-18">18. Similarity Retrieval (Top-K=4 Euclidean)</a> <span>p. 34</span></li>
            <li><a href="#sec-19">19. In-Context Grounding &amp; Anti-Hallucination</a> <span>p. 36</span></li>
            <li><a href="#sec-20">20. OpenRouter Gateway &amp; Gemini 2.5 Flash</a> <span>p. 37</span></li>
            <li><a href="#sec-21">21. Page-Level Citation Attribution</a> <span>p. 38</span></li>
          </ul>
        </div>

        <div class="toc-part-group">
          <div class="toc-part-header">PART V — ENGINEERING DEEP DIVE</div>
          <ul class="toc-list">
            <li><a href="#sec-22">22. FastAPI Concurrency &amp; Async I/O Model</a> <span>p. 40</span></li>
            <li><a href="#sec-23">23. Dependency Injection Architecture</a> <span>p. 41</span></li>
            <li><a href="#sec-24">24. Custom Error &amp; Exception Hierarchy</a> <span>p. 42</span></li>
            <li><a href="#sec-25">25. Document CRUD Lifecycle (Figure F)</a> <span>p. 43</span></li>
            <li><a href="#sec-26">26. Safe Document Replacement (Figure G)</a> <span>p. 45</span></li>
            <li><a href="#sec-27">27. Frontend Architecture &amp; Context</a> <span>p. 47</span></li>
            <li><a href="#sec-28">28. Chat History localStorage Persistence</a> <span>p. 49</span></li>
            <li><a href="#sec-29">29. Critical Code Snippets &amp; Analysis</a> <span>p. 50</span></li>
          </ul>
        </div>

        <div class="toc-part-group">
          <div class="toc-part-header">PART VI — QUALITY, SECURITY &amp; OPS</div>
          <ul class="toc-list">
            <li><a href="#sec-30">30. Testing Strategy (236 Passing Tests)</a> <span>p. 54</span></li>
            <li><a href="#sec-31">31. Security Posture (Implemented vs Future)</a> <span>p. 56</span></li>
            <li><a href="#sec-32">32. SensitiveDataFilter Logging Redaction</a> <span>p. 58</span></li>
            <li><a href="#sec-33">33. Latency Profile &amp; Bottleneck Analysis</a> <span>p. 59</span></li>
            <li><a href="#sec-34">34. Exhaustive Failure Modes Matrix</a> <span>p. 60</span></li>
            <li><a href="#sec-35">35. Deployment Architecture (Figure H)</a> <span>p. 63</span></li>
            <li><a href="#sec-36">36. Scalability Roadmap (10x to 100x Scale)</a> <span>p. 65</span></li>
          </ul>
        </div>

        <div class="toc-part-group">
          <div class="toc-part-header">PART VII — ENGINEERING JUDGEMENT</div>
          <ul class="toc-list">
            <li><a href="#sec-37">37. Core Decisions &amp; 10 Decision Cards</a> <span>p. 67</span></li>
            <li><a href="#sec-38">38. Comprehensive Trade-offs Matrix</a> <span>p. 70</span></li>
            <li><a href="#sec-39">39. Architectural Limitations &amp; Realities</a> <span>p. 73</span></li>
            <li><a href="#sec-40">40. Advanced RAG Evolution (V1 to V7)</a> <span>p. 75</span></li>
            <li><a href="#sec-41">41. RAGAS Quality Evaluation Framework</a> <span>p. 77</span></li>
          </ul>
        </div>

        <div class="toc-part-group">
          <div class="toc-part-header">PART VIII — INTERVIEW DEFENSE BANK</div>
          <ul class="toc-list">
            <li><a href="#sec-42">42. Technical Interview Questions (Q1–Q70)</a> <span>p. 79</span></li>
            <li><a href="#sec-43">43. "Why This?" Architectural Defenses</a> <span>p. 95</span></li>
            <li><a href="#sec-44">44. "What If?" Resilience Stress Scenarios</a> <span>p. 98</span></li>
            <li><a href="#sec-45">45. Authoritative REST API Reference</a> <span>p. 101</span></li>
            <li><a href="#sec-46">46. Authoritative Configuration Reference</a> <span>p. 103</span></li>
            <li><a href="#sec-47">47. File-by-File Technical Responsibilities</a> <span>p. 105</span></li>
            <li><a href="#sec-48">48. Rapid-Fire Project Defense Cheat Sheet</a> <span>p. 108</span></li>
            <li><a href="#sec-49">49. Pre-Interview Readiness Checklist</a> <span>p. 110</span></li>
          </ul>
        </div>
      </div>
    </div>
    """

print("Cover and Table of Contents generators ready.")
