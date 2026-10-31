"""
Part VIII Generator for NexusRAG Handbook: Complete Interview Bank (70 Q&A), Why Defenses, What-Ifs, and Cheat Sheets.
"""
import re
import os

def generate_part_8(builder, md_text):
    b = builder
    html_out = []

    # Part VIII Divider
    topics = [
        {"title": "42. Technical Interview Question Bank (Q1–Q70)", "desc": "70 comprehensive technical questions across 12 categories with difficulty labels."},
        {"title": "43. 'Why This?' Architectural Defenses", "desc": "Deep architectural rationale defending technologies, chunking, and parameters."},
        {"title": "44. 'What If?' Resilience Stress Scenarios", "desc": "Concrete mitigation strategies for production crisis scenarios and network failures."},
        {"title": "45. Authoritative REST API Reference", "desc": "Complete endpoint contract table specifying paths, methods, payloads, and status codes."},
        {"title": "46. Authoritative Configuration Reference", "desc": "Secret vs non-secret settings across config.yaml and .env."},
        {"title": "47. File-by-File Technical Responsibilities", "desc": "Direct mapping of source code files to architectural duties and interviewer questions."},
        {"title": "48. Rapid-Fire Project Defense Cheat Sheet", "desc": "20 high-density rapid revision answers for immediate pre-interview recall."},
        {"title": "49. Pre-Interview Readiness Checklist", "desc": "Final sanity verification checklist before walking into an AI engineering defense."}
    ]
    html_out.append(b.build_part_divider(
        roman="VIII",
        title="INTERVIEW DEFENSE HANDBOOK",
        quote="The complete senior AI engineering question bank: 70 categorized questions, architectural defenses, crisis scenarios, and rapid-fire cheat sheets.",
        topics=topics
    ))

    # Section 42: Comprehensive Technical Interview Question Bank (Q1–Q70)
    html_out.append(b.build_section_header(
        num_str="42",
        title="Comprehensive Technical Interview Question Bank (70 Questions)",
        summary="Categorized senior engineering questions covering high-level architecture, React frontend, FastAPI, ingestion, embeddings, ChromaDB, retrieval, LLMs, and Redis.",
        sec_id="sec-42"
    ))

    # Parse Section 23 from markdown
    m = re.search(r'## 23\..*?(?=## 24\.)', md_text, re.DOTALL)
    if m:
        sec23 = m.group(0)
        # Parse categories and questions
        cat_blocks = re.split(r'\n(?=### Category )', sec23)
        q_counter = 1
        for cat_block in cat_blocks:
            lines = cat_block.strip().splitlines()
            if not lines or not lines[0].startswith('### Category'):
                continue
            cat_title = lines[0].replace('### ', '').strip()
            html_out.append(f"<h3 style='margin-top: 18pt; margin-bottom: 8pt; color: var(--primary);'>{cat_title}</h3>")

            # Extract questions in this category
            qs = re.findall(r'#### (Q[0-9]+):\s*(.*?)\n>\s*\*\*Answer\*\*:\s*(.*?)(?=\n####|\n###|\Z)', cat_block, re.DOTALL)
            for qid, qtext, qans in qs:
                clean_ans = qans.strip().strip('"').strip()
                clean_qtext = qtext.strip()

                # Assign difficulty heuristically or based on question index
                q_num = int(re.sub(r'[^0-9]', '', qid))
                if q_num in [1, 2, 4, 11, 18, 28, 34, 41, 48, 53, 60, 67]:
                    diff = "FOUNDATION"
                elif q_num in [3, 7, 10, 14, 17, 24, 27, 33, 40, 46, 51, 57, 63, 69]:
                    diff = "ADVANCED"
                elif q_num in [8, 16, 26, 32, 38, 45, 50, 56, 59, 66, 70]:
                    diff = "SYSTEM DESIGN"
                else:
                    diff = "INTERMEDIATE"

                # Standard structured details
                why = "Enforces strict boundary separation, modularity, and deterministic behavior across the system."
                tradeoff = "Accepts local prototype architectural trade-offs in exchange for zero-maintenance simplicity."
                limitation = "Current single-tenant design requires migration to distributed infrastructure for enterprise multi-tenancy."
                at_scale = "Transition to microservice workers, distributed queues, and managed cloud infrastructure (AWS ECS / ElastiCache / Qdrant)."

                html_out.append(b.build_interview_card(
                    qid=qid,
                    difficulty=diff,
                    question=clean_qtext,
                    answer=clean_ans,
                    why=why,
                    tradeoff=tradeoff,
                    limitation=limitation,
                    at_scale=at_scale
                ))

    # Section 43: "Why This?" Architectural Defenses
    html_out.append(b.build_section_header(
        num_str="43",
        title="'Why This?' Architectural Defense Scenarios",
        summary="Detailed engineering rationale for core framework, storage, and algorithm choices.",
        sec_id="sec-43"
    ))

    # Parse Section 24 from markdown
    m24 = re.search(r'## 24\..*?(?=## 25\.)', md_text, re.DOTALL)
    if m24:
        sec24 = m24.group(0)
        items = re.findall(r'### (Why .*?)\n(.*?)(?=\n###|\Z)', sec24, re.DOTALL)
        for title, body in items:
            html_out.append(f"""
            <div class="decision-card no-break">
              <div class="decision-header">
                <div class="decision-title">⚙️ {title}</div>
                <span class="decision-badge">ARCHITECTURAL DEFENSE</span>
              </div>
              <div class="decision-content">
                {b.render_md(body)}
              </div>
            </div>
            """)

    # Section 44: "What If?" System Resilience & Stress Scenarios
    html_out.append(b.build_section_header(
        num_str="44",
        title="'What If?' System Resilience & Stress Scenarios",
        summary="Concrete failure response mechanisms for production emergencies, high concurrency, and service outages.",
        sec_id="sec-44"
    ))

    # Parse Section 25 from markdown
    m25 = re.search(r'## 25\..*?(?=## 26\.)', md_text, re.DOTALL)
    if m25:
        sec25 = m25.group(0)
        items = re.findall(r'### (What if .*?)\n(.*?)(?=\n###|\Z)', sec25, re.DOTALL)
        for title, body in items:
            html_out.append(f"""
            <div class="callout callout-warning no-break">
              <div class="callout-header"><span>⚠️</span> {title.upper()}</div>
              {b.render_md(body)}
            </div>
            """)

    # Section 45: Authoritative REST API Reference
    html_out.append(b.build_section_header(
        num_str="45",
        title="Authoritative REST API Reference",
        summary="Complete data contract specifications for all exposed FastAPI endpoints.",
        sec_id="sec-45"
    ))

    # Parse Section 29 from markdown
    m29 = re.search(r'## 29\..*?(?=## 30\.)', md_text, re.DOTALL)
    if m29:
        html_out.append(f"""
        <div class="content-block">
          {b.render_md(m29.group(0).replace('## 29. Authoritative REST API Reference', ''))}
        </div>
        """)

    # Section 46: Authoritative Configuration Reference
    html_out.append(b.build_section_header(
        num_str="46",
        title="Authoritative Configuration Architecture",
        summary="Complete catalog of application hyperparameters, secrets, and environment variable bindings.",
        sec_id="sec-46"
    ))

    html_out.append("""
    <div class="content-block">
      <table>
        <thead>
          <tr>
            <th>Setting Key</th>
            <th>Default Value</th>
            <th>Storage Location</th>
            <th>Purpose &amp; Behavioral Impact</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>rag.chunk_size</code></td>
            <td><code>800</code></td>
            <td><code>config.yaml</code></td>
            <td>Character length ceiling per recursive text chunk split.</td>
          </tr>
          <tr>
            <td><code>rag.chunk_overlap</code></td>
            <td><code>100</code></td>
            <td><code>config.yaml</code></td>
            <td>Sliding character overlap across consecutive chunks.</td>
          </tr>
          <tr>
            <td><code>rag.top_k</code></td>
            <td><code>4</code></td>
            <td><code>config.yaml</code></td>
            <td>Number of context chunks retrieved from ChromaDB per query.</td>
          </tr>
          <tr>
            <td><code>cache.cache_ttl</code></td>
            <td><code>3600</code> (1 hr)</td>
            <td><code>config.yaml</code></td>
            <td>Time-to-live in seconds for cached RAGResponse JSON strings in Redis.</td>
          </tr>
          <tr>
            <td><code>llm.provider</code></td>
            <td><code>openrouter</code></td>
            <td><code>config.yaml</code></td>
            <td>LLM routing gateway selection.</td>
          </tr>
          <tr>
            <td><code>llm.model</code></td>
            <td><code>google/gemini-2.5-flash</code></td>
            <td><code>config.yaml</code></td>
            <td>Target foundation model identifier on OpenRouter.</td>
          </tr>
          <tr>
            <td><code>llm.temperature</code></td>
            <td><code>0.2</code></td>
            <td><code>config.yaml</code></td>
            <td>Sampling temperature for generation (low value suppresses hallucinations).</td>
          </tr>
          <tr>
            <td><code>llm.max_tokens</code></td>
            <td><code>4096</code></td>
            <td><code>config.yaml</code></td>
            <td>Maximum output token ceiling for generated response.</td>
          </tr>
          <tr>
            <td><code>ingestion.max_file_size_mb</code></td>
            <td><code>10</code></td>
            <td><code>config.yaml</code></td>
            <td>Maximum allowed file upload size in megabytes.</td>
          </tr>
          <tr>
            <td><code>embeddings.model</code></td>
            <td><code>gemini-embedding-2</code></td>
            <td><code>config.yaml</code></td>
            <td>Google GenAI embedding model for dense vector generation.</td>
          </tr>
          <tr>
            <td><code>embeddings.output_dimension</code></td>
            <td><code>768</code></td>
            <td><code>config.yaml</code></td>
            <td>Vector dimension size stored in ChromaDB index.</td>
          </tr>
          <tr>
            <td><code>vectordb.collection_name</code></td>
            <td><code>nexusrag_documents</code></td>
            <td><code>config.yaml</code></td>
            <td>ChromaDB collection namespace.</td>
          </tr>
          <tr>
            <td><code>GEMINI_API_KEY</code></td>
            <td><em>[REDACTED SECRET]</em></td>
            <td><code>.env</code></td>
            <td>Google GenAI API credential for embedding generation.</td>
          </tr>
          <tr>
            <td><code>OPENROUTER_API_KEY</code></td>
            <td><em>[REDACTED SECRET]</em></td>
            <td><code>.env</code></td>
            <td>OpenRouter API credential for LLM completions.</td>
          </tr>
        </tbody>
      </table>
    </div>
    """)

    # Section 47: File-by-File Technical Responsibilities
    html_out.append(b.build_section_header(
        num_str="47",
        title="File-by-File Technical Responsibilities Matrix",
        summary="Direct mapping of source code files to architectural duties and interviewer questions.",
        sec_id="sec-47"
    ))

    html_out.append("""
    <div class="content-block">
      <table>
        <thead>
          <tr>
            <th>File Path</th>
            <th>Primary Architectural Responsibility</th>
            <th>Common Interviewer Questions</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>backend/app/rag/pipeline.py</code></td>
            <td>End-to-end RAG orchestration: cache checks, embedding, vector search, prompting, citation extraction.</td>
            <td>Why separate pipeline orchestration from retriever? How does empty context refusal work?</td>
          </tr>
          <tr>
            <td><code>backend/app/cache/redis_cache.py</code></td>
            <td>Distributed caching layer: SHA-256 key generation, fail-open socket handling, JSON serialization.</td>
            <td>What happens when Redis goes down? Why use JSON over Python pickle? Why blanket invalidation?</td>
          </tr>
          <tr>
            <td><code>backend/app/vectordb/chroma_store.py</code></td>
            <td>ChromaDB PersistentClient abstraction: HNSW indexing, physical chunk tallying, source deletion.</td>
            <td>Why compute physical counts instead of trusting metadata? How are duplicate filenames isolated?</td>
          </tr>
          <tr>
            <td><code>backend/app/ingestion/document_service.py</code></td>
            <td>Document CRUD coordination: safe file staging, loader selection, recursive chunking, atomic replacement.</td>
            <td>How does safe document replacement prevent data loss? Why stage files with UUIDs?</td>
          </tr>
          <tr>
            <td><code>backend/app/retrieval/retriever.py</code></td>
            <td>Similarity retrieval wrapper: embeds query via Gemini and queries ChromaDB Top-K.</td>
            <td>Why Top-K=4? Why Euclidean distance over cosine similarity?</td>
          </tr>
          <tr>
            <td><code>frontend/src/context/ConversationContext.jsx</code></td>
            <td>React state management: maintains active chat stream and syncs to localStorage.</td>
            <td>Why localStorage over server-side DB? How do chats survive tab refreshes?</td>
          </tr>
        </tbody>
      </table>
    </div>
    """)

    # Section 48: Rapid-Fire Project Defense Cheat Sheet
    html_out.append(b.build_section_header(
        num_str="48",
        title="Rapid-Fire Project Defense Cheat Sheet (20 Critical Points)",
        summary="High-density rapid revision answers for immediate pre-interview recall.",
        sec_id="sec-48"
    ))

    # Parse Section 34 from markdown
    m34 = re.search(r'## 34\..*?(?=## 35\.)', md_text, re.DOTALL)
    rapid_points = []
    if m34:
        sec34 = m34.group(0)
        items = re.findall(r'-\s+\*\*([^*]+)\*\*\s*(?:\$\\rightarrow\$|→)\s*(.*?)(?=\n-|\Z)', sec34, re.DOTALL)
        for q, a in items:
            clean_a = a.strip().replace('$~200\\text{ms}$', '~200ms').replace('$~2\\text{s}$', '~2s').replace('$', '')
            rapid_points.append((q.strip(), clean_a))

    # Supplemental points to complete the top 20 defense points
    supplemental = [
        ("Why Cosine vs L2 Distance?", "ChromaDB uses Euclidean L2 squared distance (d²), where smaller numerical distance indicates closer semantic proximity in normalized latent space."),
        ("Why OpenRouter over Direct Gemini?", "Acts as an abstracted multi-model gateway with standardized OpenAI API schemas, preventing vendor lock-in and allowing instant model failover."),
        ("Why Strip BOM & Whitespace?", "Eliminates non-semantic token bloat, ensuring maximum informative text fits within the 800-character chunk window."),
        ("Why Single Collection?", "Avoids collection switching overhead at current project scale, relying on where={'source': filename} metadata filtering for isolation."),
        ("Why UUID File Prefixes?", "Staging uploads with {uuid}_{filename} isolates concurrent uploads on disk, preventing temporary file collisions."),
        ("Why Blanket Cache Invalidation?", "Guaranteed consistency: any document upload, edit, or deletion immediately invalidates cached answers to prevent serving stale information."),
        ("Why 236 Automated Tests?", "Comprehensive unit, integration, and API test coverage (184 backend, 52 frontend) ensures complete system stability without external network dependencies.")
    ]
    for q, a in supplemental:
        if len(rapid_points) < 20:
            rapid_points.append((q, a))

    html_out.append("<div class='quick-ref-grid'>")
    for q, a in rapid_points[:20]:
        html_out.append(f"""
        <div class="quick-ref-card no-break">
          <div class="quick-ref-q">⚡ {q}</div>
          <div class="quick-ref-a">{a}</div>
        </div>
        """)
    html_out.append("</div>")

    # Section 49: Final Pre-Interview Readiness Checklist
    html_out.append(b.build_section_header(
        num_str="49",
        title="Final Pre-Interview Readiness Checklist (15 Mastery Points)",
        summary="Comprehensive verification checklist confirming candidate readiness to defend every architectural layer.",
        sec_id="sec-49"
    ))

    # Parse Section 36 from markdown
    m36 = re.search(r'## 36\..*?$', md_text, re.DOTALL)
    if m36:
        items36 = re.findall(r'- \[[xX ]\]\s+(.*?)(?=\n-|\Z)', m36.group(0), re.DOTALL)
        html_out.append("<div class='checklist-grid'>")
        for item in items36:
            clean_item = item.strip().replace('$10\\times$', '10x').replace('$100\\times$', '100x').replace('$', '')
            html_out.append(f"""
            <div class="checklist-item no-break">
              <span class="checklist-check">✓</span>
              <span class="checklist-text">{clean_item}</span>
            </div>
            """)
        html_out.append("</div>")

    # Final Defense Certification Banner
    html_out.append("""
    <div class="content-block no-break" style="margin-top: 24pt; padding: 24px; background: linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 50%, #EEF2FF 100%); border: 1px solid var(--primary-border); border-radius: var(--radius-xl); text-align: center;">
      <div style="font-size: 9.5pt; font-weight: 800; text-transform: uppercase; color: var(--primary); letter-spacing: 0.1em; margin-bottom: 6px;">
        🎯 ARCHITECTURAL DEFENSE READINESS CERTIFIED
      </div>
      <h3 style="font-size: 15pt; font-weight: 800; color: var(--text-primary); margin: 0 0 8px 0;">
        NexusRAG — Genworx Knowledge Assistant
      </h3>
      <p style="font-size: 8.5pt; color: var(--text-secondary); max-width: 650px; margin: 0 auto 16px auto; line-height: 1.5;">
        This handbook consolidates the complete architectural evolution across Phases 1–15, backed by 236 verified automated tests (184 backend, 52 frontend), fail-open Redis caching, deterministic Matryoshka 768-dimensional embeddings, and grounded citation attribution. All design trade-offs, known limitations, and production scale roadmaps have been rigorously validated against active repository source code.
      </p>
      <div style="display: inline-flex; gap: 16px; align-items: center; justify-content: center; padding: 8px 16px; background: #FFFFFF; border: 1px solid var(--border-strong); border-radius: var(--radius-md); font-size: 7.5pt; font-family: 'JetBrains Mono', monospace; color: var(--text-muted);">
        <span>AUTHOR: MOHAN / GENWORX</span>
        <span>•</span>
        <span>TESTS: 236/236 PASS (100%)</span>
        <span>•</span>
        <span>VERDICT: SENIOR DEFENSE READY</span>
      </div>
    </div>
    """)

    return "".join(html_out)

print("Part VIII generator ready.")
