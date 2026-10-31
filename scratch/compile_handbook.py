"""
Master Compilation Script for NexusRAG Project Defense Handbook.
Reads GENWORX_RAG_INTERVIEW_PREPARATION.md, synthesizes all 8 Parts, inlines SVG diagrams,
embeds CSS, renders HTML, and uses Playwright to generate the high-resolution interactive PDF.
"""
import os
import sys
import re
import html
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
def build_part_divider(part_num, roman, title, quote, topics):
    topics_html = "".join([f"""
    <div class="part-topic-item">
      <h4>{t['title']}</h4>
      <p>{t['desc']}</p>
    </div>
    """ for t in topics])

    return f"""
    <div class="part-divider" id="part-{roman.lower()}">
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

print("Base compilation logic defined.")
