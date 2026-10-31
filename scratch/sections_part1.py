"""
Part I Generator for NexusRAG Handbook: Project Story, User Stories, and Pitches.
"""

def generate_part_1(builder):
    b = builder
    html_out = []

    # Part I Divider
    topics = [
        {"title": "01. Executive Overview & Problem Definition", "desc": "What is NexusRAG, the hallucination problem, institutional freshness, and target users."},
        {"title": "02. End-to-End User Story Flows", "desc": "Flows A through S overview, and detailed cards for core implemented user journeys."},
        {"title": "03. Executive Pitches & Walkthroughs", "desc": "30-second elevator pitch, 2-minute interview pitch, and 5-minute technical deep dive."}
    ]
    html_out.append(b.build_part_divider(
        roman="I",
        title="PROJECT STORY & MOTIVATION",
        quote="How NexusRAG transforms private, rapidly changing enterprise documents into a dependable, citation-backed AI assistant.",
        topics=topics
    ))

    # Section 01: Executive Overview & Problem Solved
    html_out.append(b.build_section_header(
        num_str="01",
        title="Executive Overview & Problem Solved",
        summary="NexusRAG is a production-aligned Retrieval-Augmented Generation system that eliminates LLM hallucinations and bridges institutional knowledge freshness.",
        sec_id="sec-01"
    ))

    html_out.append("""
    <div class="content-block">
      <h3>1.1 What is NexusRAG?</h3>
      <p>
        <strong>NexusRAG (Genworx Knowledge Assistant)</strong> is an enterprise-grade AI assistant engineered to perform grounded question-answering over private institutional documents. Built on a modern decoupled stack—<strong>React 18</strong> single-page frontend, <strong>FastAPI</strong> asynchronous backend, <strong>ChromaDB</strong> vector database, <strong>Redis</strong> distributed query cache, <strong>Google Gemini Embedding 2</strong>, and <strong>Google Gemini 2.5 Flash</strong> via the <strong>OpenRouter API gateway</strong>—NexusRAG enables knowledge workers to upload internal documents (PDFs, Markdown, text files) and query them through a natural-language chat interface with strict citation attribution.
      </p>

      <h3>1.2 Core Business Problems Solved</h3>
      <p>
        General-purpose foundation models (e.g., ChatGPT, Claude, Gemini) suffer from three fundamental architectural limitations when applied to enterprise workflows:
      </p>
      <ul>
        <li><strong>LLM Hallucinations:</strong> Foundation models generate plausible-sounding but factually fabricated statements when answering questions outside their training data or when probabilistic token sampling drifts.</li>
        <li><strong>Training Cutoff &amp; Static Knowledge:</strong> Foundation models possess static weights frozen at training time. They are completely blind to company-specific policies, internal handbooks, project specifications, and recent updates.</li>
        <li><strong>Absence of Verifiable Citations:</strong> Off-the-shelf LLMs cannot provide verifiable document and page-level provenance. Users cannot confirm whether an answer is grounded in an official company document.</li>
      </ul>
      <p>
        NexusRAG resolves these failure modes by decoupling <em>reasoning</em> from <em>memory</em>. The LLM acts strictly as a reasoning engine over external context retrieved deterministically from a local vector store.
      </p>

      <h3>1.3 Target Audience &amp; Personas</h3>
      <table>
        <thead>
          <tr>
            <th>Persona</th>
            <th>Primary Objective</th>
            <th>NexusRAG Value Proposition</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Enterprise Knowledge Worker</strong></td>
            <td>Rapidly locate company policies, technical specifications, and procedural guidelines.</td>
            <td>Sub-2-second answers with exact source filename and page numbers, eliminating manual document scanning.</td>
          </tr>
          <tr>
            <td><strong>System Administrator &amp; Auditor</strong></td>
            <td>Ensure organizational answers comply with official documentation and audit trails.</td>
            <td>Anti-hallucination prompt constraints force the model to refuse to answer if supporting context is absent.</td>
          </tr>
          <tr>
            <td><strong>DevOps / AI Engineer</strong></td>
            <td>Operate a cost-efficient, resilient, observable AI service with low operational complexity.</td>
            <td>Sub-10ms Redis query caching, fail-open resilience, 100% test isolation, and zero external DB clustering overhead.</td>
          </tr>
        </tbody>
      </table>
    </div>
    """)

    # Diagram I: Naive LLM vs Grounded RAG
    html_out.append(b.build_diagram_box(
        fig_num="I",
        title="Naive Foundation LLM vs NexusRAG Grounded Architecture",
        svg_name="diagram_i_rag_vs_naive_llm.svg",
        what="Side-by-side comparison between an ungrounded foundation model call and NexusRAG's dense retrieval-augmented generation pipeline.",
        how="In naive LLMs, questions pass directly to model weights. In NexusRAG, queries are embedded, matched against indexed vectors, and injected into a strict grounding prompt.",
        why="Decoupling knowledge storage from model weights allows real-time document updates, zero training costs, and deterministic source attribution.",
        interview_point="RAG is not just 'search plus prompt'—it is an architectural contract ensuring the model refuses to answer when information is absent."
    ))

    # Section 02: End-to-End User Story Flows
    html_out.append(b.build_section_header(
        num_str="02",
        title="Implemented User Story Flows & Personas",
        summary="Exhaustive breakdown of end-to-end user journeys implemented across Phases 1 through 15.",
        sec_id="sec-02"
    ))

    html_out.append("""
    <div class="content-block">
      <p>
        NexusRAG implements 19 discrete architectural flows (Flows A through S) covering client bootstrapping, document lifecycle management, dense retrieval, and cache synchronization:
      </p>
      <table>
        <thead>
          <tr>
            <th>Flow ID</th>
            <th>User / System Flow</th>
            <th>Primary Components Involved</th>
            <th>Verified Status</th>
          </tr>
        </thead>
        <tbody>
          <tr><td><strong>Flow A</strong></td><td>User Opens Application</td><td>React 18 · Vite · ConversationContext · localStorage</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow B</strong></td><td>User Uploads Document</td><td>DocumentsPage · api.js · POST /api/v1/upload · IngestionConfig</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow C</strong></td><td>Document Ingestion &amp; Parsing</td><td>DocumentService · PyPDFLoader · TextLoader · helpers.clean_text</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow D</strong></td><td>Document Chunking</td><td>RecursiveCharacterTextSplitter · chunk_size=800 · overlap=100</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow E</strong></td><td>Batch Embedding Generation</td><td>GeminiEmbeddingService · gemini-embedding-2 · 768-dim · Batch 100</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow F</strong></td><td>ChromaDB Vector Indexing</td><td>ChromaStore · PersistentClient · SQLite · HNSW Euclidean Index</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow G</strong></td><td>User Submits Question</td><td>ChatPage · ChatInput · useChat · POST /api/v1/chat</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow H</strong></td><td>Redis Cache Resolution (HIT)</td><td>RedisQueryCache · SHA-256 Key · Deserialization · Sub-10ms Return</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow I</strong></td><td>Redis Cache Resolution (MISS)</td><td>RedisQueryCache · Fall-through to Vector Retrieval &amp; LLM</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow J</strong></td><td>Query Embedding Generation</td><td>GeminiEmbeddingService · embed_query() · 768-dim Query Vector</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow K</strong></td><td>Similarity Vector Retrieval</td><td>Retriever · ChromaStore · Top-K=4 · Euclidean Squared Distance</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow L</strong></td><td>In-Context Prompt Construction</td><td>templates.py · Context formatting · Anti-hallucination directive</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow M</strong></td><td>LLM Completion Generation</td><td>OpenRouterLLMService · ChatOpenAI · google/gemini-2.5-flash</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow N</strong></td><td>Citation Attribution &amp; Deduplication</td><td>RAGPipeline · (source, page) tuple deduplication</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow O</strong></td><td>Conversation Persistence</td><td>ConversationContext · localStorage key: nexusrag:chat-history:v1</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow P</strong></td><td>New Conversation Reset</td><td>Navbar "+ New Chat" · Clears active messages · Keeps storage</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow Q</strong></td><td>Safe Document Replacement</td><td>routes_documents.py · Stage -&gt; Ingest -&gt; Delete Old -&gt; Clear Cache</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow R</strong></td><td>Document Deletion &amp; Invalidation</td><td>ChromaStore.delete_by_source() · redis_cache.clear()</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
          <tr><td><strong>Flow S</strong></td><td>Application Health &amp; Lifespan</td><td>routes_health.py · GET /api/v1/health · Config validation</td><td><span class="status-badge implemented">IMPLEMENTED</span></td></tr>
        </tbody>
      </table>
    </div>
    """)

    # User Story Cards for Core Flows
    html_out.append(b.build_user_story_card(
        flow_id="US-01",
        title="Document Upload & Automated Indexing",
        actor="Knowledge Base Administrator",
        trigger="Admin selects and uploads a PDF, TXT, or MD document in DocumentsPage.",
        preconditions="Document size <= 10MB; valid file extension; backend is healthy.",
        technical_steps=[
            "DocumentsPage sends multipart/form-data POST to /api/v1/upload.",
            "Backend validates extension and size, then stages file to ./data/uploads/{uuid}_{filename}.",
            "DocumentService selects appropriate loader (PyPDFLoader for PDF, TextLoader for text/markdown).",
            "Extracted text is sanitized via helpers.clean_text (whitespace normalization, empty check).",
            "RecursiveCharacterTextSplitter splits text into 800-character chunks with 100-character overlap.",
            "GeminiEmbeddingService batches chunks (size 100) and calls gemini-embedding-2 for 768-dim vectors.",
            "ChromaStore upserts vectors and metadata into collection nexusrag_documents.",
            "Redis query cache is purged to prevent stale answers; staged upload file is unlinked in finally block."
        ],
        result="Document appears in document table with verified physical chunk count and timestamp.",
        failure_cases="File > 10MB (413); invalid extension (400); zero extractable text (422); embedding 429 (502)."
    ))

    html_out.append(b.build_user_story_card(
        flow_id="US-02",
        title="Grounded Question Answering with Citations",
        actor="Knowledge Worker",
        trigger="User types a natural-language question into ChatInput and presses Enter.",
        preconditions="At least one document has been indexed into ChromaDB; Redis and LLM gateway reachable.",
        technical_steps=[
            "ChatInput dispatches question through useChat hook to services/api.js.",
            "HTTP POST /api/v1/chat sends JSON payload { 'query': '...' } to FastAPI.",
            "routes_chat.py receives request, validates schema, and invokes RAGPipeline.query().",
            "RAGPipeline normalizes query and checks RedisQueryCache.get() (returns in <10ms on HIT).",
            "On MISS: Retriever calls GeminiEmbeddingService.embed_query() to produce a 768-dim vector.",
            "ChromaStore performs similarity search using Euclidean distance and returns Top-K=4 chunks.",
            "Empty context check: if 0 chunks retrieved, pipeline returns deterministic refusal without calling LLM.",
            "Grounded prompt template formats retrieved chunks with source and page markers.",
            "OpenRouterLLMService sends prompt to google/gemini-2.5-flash (temperature 0.2, max_tokens 4096).",
            "Citations are extracted and deduplicated at the (source, page) level.",
            "Response is serialized to JSON and stored in Redis with TTL=3600 seconds.",
            "HTTP 200 JSON RAGResponse returned to React UI; ConversationContext appends answer to chat history."
        ],
        result="User receives a factually grounded answer with clickable source and page badges.",
        failure_cases="Empty query (422); Redis down (fail-open to RAG); LLM quota exceeded (502)."
    ))

    html_out.append(b.build_user_story_card(
        flow_id="US-05",
        title="Safe Document Replacement (Atomic Re-indexing)",
        actor="Knowledge Base Administrator",
        trigger="Admin selects 'Replace Document' for an existing file with a newer version.",
        preconditions="Target document currently exists in the knowledge base; new file passes validation.",
        technical_steps=[
            "Frontend dispatches PUT /api/v1/documents/{filename} with new file payload.",
            "routes_documents.py verifies target document exists in ChromaDB (returns 404 if absent).",
            "New file is saved to an isolated staged path: ./data/uploads/{uuid}_{filename}.",
            "New file is ingested, parsed, chunked, embedded, and indexed into ChromaDB FIRST.",
            "If indexing fails: staged file is removed, old vectors are KEPT INTACT in ChromaDB, error returned.",
            "If indexing succeeds: backend queries and purges all old vectors matching the target filename.",
            "Entire Redis query cache is cleared to eliminate stale answers based on the old version.",
            "Staged file is deleted; HTTP 200 OK returned with updated chunk count and timestamp."
        ],
        result="Knowledge base seamlessly transitions to new document version with zero data loss on failure.",
        failure_cases="Target missing (404); replacement embedding timeout (502; old document preserved)."
    ))

    # Section 03: Executive Verbal Pitches
    html_out.append(b.build_section_header(
        num_str="03",
        title="Executive Verbal Pitches & Deep Dive Scripts",
        summary="Verbatim spoken responses engineered for senior AI engineering interviews and project defenses.",
        sec_id="sec-03"
    ))

    html_out.append("""
    <div class="content-block">
      <h3>3.1 30-Second Elevator Pitch</h3>
      <div class="callout callout-tip no-break">
        <div class="callout-header"><span>💡</span> SPOKEN VERBATIM (30 SECONDS)</div>
        <p>
          "I built NexusRAG, an enterprise knowledge assistant that solves LLM hallucinations and information freshness by connecting foundation models to private organizational documents. The architecture combines a React 18 frontend, a FastAPI asynchronous backend, ChromaDB for dense vector storage, and Redis for distributed query caching. When a user asks a question, we check Redis in sub-10 milliseconds. On a cache miss, we embed the query using Google Gemini Embedding 2, retrieve the top 4 chunks from ChromaDB, inject them into a strict grounding prompt, and generate citation-backed answers via Gemini 2.5 Flash on OpenRouter. The system features fail-open caching, atomic-like document replacement, and 236 automated tests across backend and frontend."
        </p>
      </div>

      <h3>3.2 2-Minute Technical Interview Pitch</h3>
      <div class="callout callout-tip no-break">
        <div class="callout-header"><span>💡</span> SPOKEN VERBATIM (2 MINUTES)</div>
        <p>
          "In many enterprise settings, teams struggle with institutional knowledge scattered across PDFs, release notes, and internal wikis. Foundation models can't see this private data and tend to hallucinate plausible untruths. I architected NexusRAG to solve this with a production-aligned RAG pipeline.
        </p>
        <p>
          On the ingestion side, documents are staged safely, parsed using PyPDFLoader or TextLoader, sanitized, and split into 800-character chunks with 100-character overlap using recursive character splitting. We batch chunks in groups of 100 and generate 768-dimensional dense embeddings using Google's Gemini Embedding 2, storing them in ChromaDB with persistent SQLite metadata and HNSW vector indexing.
        </p>
        <p>
          On the query side, requests hit a FastAPI ASGI service. We first check Redis using a normalized SHA-256 hash key. If cached, we return the deserialized response in 5 to 10 milliseconds. If not, we generate a query embedding, retrieve the top 4 chunks using Euclidean distance, and pass them into our grounded QA prompt. Gemini 2.5 Flash processes the completion with temperature 0.2, and we extract deduplicated source and page citations.
        </p>
        <p>
          Key engineering decisions include: fail-open Redis caching so cache downtime never causes user outages; a safe document replacement protocol that embeds new files before deleting old vectors to prevent data loss; physical chunk counting to prevent metadata drift; and 236 automated tests achieving end-to-end API isolation with test doubles."
        </p>
      </div>

      <h3>3.3 5-Minute Technical Deep Dive Walkthrough</h3>
      <p>
        For senior system design rounds, structure your 5-minute explanation sequentially across these eight architectural layers:
      </p>
      <ol>
        <li><strong>Client &amp; Persistence Layer:</strong> React 18 SPA built with Vite, utilizing a centralized <code>ConversationContext</code> backed by browser <code>localStorage</code> under key <code>nexusrag:chat-history:v1</code>, allowing multi-turn conversations to survive page reloads.</li>
        <li><strong>API &amp; Concurrency Model:</strong> FastAPI running on Uvicorn ASGI. Endpoints use asynchronous defs for I/O operations and route blocking synchronous tasks (like ChromaDB disk writes) to AnyIO thread pools to keep the event loop responsive.</li>
        <li><strong>Ingestion &amp; Chunking Strategy:</strong> File staging to isolated paths prevents race conditions. Text is normalized and split with <code>chunk_size=800</code> and <code>chunk_overlap=100</code> to balance semantic coherence against prompt context window saturation.</li>
        <li><strong>Vector Embeddings:</strong> Google Gemini Embedding 2 with 768 output dimensions and batch size 100. Overcomes OpenAI rate limits while providing superior retrieval accuracy for asymmetric query-document matching.</li>
        <li><strong>Vector Storage &amp; Physical Counting:</strong> ChromaDB PersistentClient. We enforce physical vector counting as the single source of truth for document chunk tallies, preventing UI metadata masking.</li>
        <li><strong>Distributed Query Caching:</strong> Redis distributed cache with SHA-256 query keys and 3600-second TTL. Implements fail-open exception handling: socket timeouts log a warning and fall through to RAG without failing the query.</li>
        <li><strong>LLM Reasoning Gateway:</strong> OpenRouter gateway routing to Google Gemini 2.5 Flash with sampling temperature 0.2. Automatic exponential backoff retries transient 429/5xx errors up to 3 times.</li>
        <li><strong>Operational Rigor &amp; Testing:</strong> 184 backend Pytest unit and integration tests + 52 frontend Vitest tests (236 total, 100% passing). Complete test doubles for Redis, ChromaDB, and model APIs guarantee zero external network dependencies during automated CI/CD runs.</li>
      </ol>
    </div>
    """)

    return "".join(html_out)

print("Part I generator ready.")
