"""
Part II Generator for NexusRAG Handbook: System Architecture and Component Design.
"""

def generate_part_2(builder):
    b = builder
    html_out = []

    # Part II Divider
    topics = [
        {"title": "04. Architecture Overview & Stat Cards", "desc": "Key hyperparameter metrics, engineering guarantees, and architectural principles."},
        {"title": "05. Master System Architecture (Figure A)", "desc": "Multi-tier layered system diagram spanning Client, API, Domain, Cache, and Storage."},
        {"title": "06. Low-Level Component Layout (Figure E)", "desc": "FastAPI dependency injection graph, domain orchestrators, and service abstractions."},
        {"title": "07. End-to-End Request Lifecycle (Figure J)", "desc": "15-step technical trace of a question from React UI to Gemini 2.5 Flash and back."},
        {"title": "08. Complete Project Folder Structure", "desc": "File-by-file directory breakdown and responsibilities matrix."}
    ]
    html_out.append(b.build_part_divider(
        roman="II",
        title="SYSTEM ARCHITECTURE & DATA FLOW",
        quote="The architectural blueprint bridging client interactions, async API routing, domain orchestration, vector storage, and external AI gateways.",
        topics=topics
    ))

    # Section 04: Architecture Overview & Key Metrics
    html_out.append(b.build_section_header(
        num_str="04",
        title="System Architecture Overview & At-a-Glance Metrics",
        summary="Verified architectural hyperparameters and operational limits established across configuration and runtime contracts.",
        sec_id="sec-04"
    ))

    # Stat cards grid
    html_out.append("""
    <div class="stat-grid">
    """)
    html_out.append(b.build_stat_card("800", "CHUNK SIZE", "Characters per recursive text split"))
    html_out.append(b.build_stat_card("100", "CHUNK OVERLAP", "Sliding window boundary context"))
    html_out.append(b.build_stat_card("4", "TOP-K CHUNKS", "Retrieved context chunks per query"))
    html_out.append(b.build_stat_card("3600s", "REDIS TTL", "Cache expiration (1 hour)"))
    html_out.append(b.build_stat_card("10 MB", "MAX FILE SIZE", "Upload ceiling for PDF/TXT/MD"))
    html_out.append(b.build_stat_card("768", "EMBEDDING DIM", "Google Gemini Embedding 2 vectors"))
    html_out.append(b.build_stat_card("0.2", "TEMPERATURE", "Low temperature for strict grounding"))
    html_out.append(b.build_stat_card("4096", "MAX TOKENS", "Gemini 2.5 Flash token ceiling"))
    html_out.append(b.build_stat_card("3", "MAX RETRIES", "Exponential backoff on 429/5xx"))
    html_out.append(b.build_stat_card("60s", "TIMEOUT", "Network request abort limit"))
    html_out.append("""
    </div>
    """)

    html_out.append("""
    <div class="content-block">
      <h3>4.1 Architectural Design Principles</h3>
      <ul>
        <li><strong>Strict Layered Decoupling:</strong> API routes never touch ChromaDB or external APIs directly. All domain operations pass through <code>RAGPipeline</code> or <code>DocumentService</code>, which consume abstract interfaces for vector storage, caching, and model completion.</li>
        <li><strong>Fail-Open Resilience:</strong> Non-critical infrastructure failures (such as Redis downtime) gracefully degrade performance without stopping core question-answering functionality.</li>
        <li><strong>Deterministic Data Contracts:</strong> Strict Pydantic models validate incoming payloads and outgoing responses at the API boundary, rejecting malformed queries before downstream execution.</li>
        <li><strong>Test Double Isolation:</strong> The entire backend can be tested in offline mode using mock LLMs, in-memory fake Redis, and ephemeral ChromaDB collections.</li>
      </ul>
    </div>
    """)

    # Section 05: Master System Architecture (Figure A)
    html_out.append(b.build_section_header(
        num_str="05",
        title="Master System Architecture",
        summary="High-level architectural blueprint detailing the 6 horizontal tiers from client browser to external model gateways.",
        sec_id="sec-05"
    ))

    html_out.append(b.build_diagram_box(
        fig_num="A",
        title="NexusRAG Master System Architecture",
        svg_name="diagram_a_master_architecture.svg",
        what="Six-tier architectural layout comprising Client Layer, FastAPI ASGI Gateway, Domain Orchestrators, Service Abstractions, Local Storage & Cache, and External AI Gateways.",
        how="HTTP requests flow from the React SPA into FastAPI endpoints. Endpoints invoke domain orchestrators via dependency injection. Orchestrators coordinate Redis caching, Gemini embeddings, ChromaDB retrieval, and OpenRouter LLM completions.",
        why="Separating routing, domain logic, and infrastructure adapters allows independent unit testing, mock injection, and zero-downtime database migrations.",
        interview_point="FastAPI serves purely as an asynchronous API controller; all retrieval and generation workflows are encapsulated in the RAGPipeline domain object."
    ))

    # Section 06: Low-Level Component Layout (Figure E)
    html_out.append(b.build_section_header(
        num_str="06",
        title="Low-Level Backend Component Architecture",
        summary="Internal class dependencies, dependency injection providers, and abstraction boundaries inside the FastAPI application.",
        sec_id="sec-06"
    ))

    html_out.append(b.build_diagram_box(
        fig_num="E",
        title="Low-Level Backend Component Dependencies & Injection Graph",
        svg_name="diagram_e_backend_components.svg",
        what="Detailed component interaction diagram showing how dependencies.py instantiates singletons and injects them into routes_chat.py, routes_documents.py, and domain pipelines.",
        how="FastAPI's Depends() mechanism resolves get_rag_pipeline() and get_document_service() by injecting shared instances of ChromaStore, RedisQueryCache, GeminiEmbeddingService, and OpenRouterLLMService.",
        why="Eliminates global state and circular imports while enabling clean test overrides in pytest via app.dependency_overrides.",
        interview_point="Singleton instances are decorated with @lru_cache, ensuring database connections and HTTP clients are instantiated once during application lifespan."
    ))

    # Section 07: End-to-End Request Lifecycle (Figure J)
    html_out.append(b.build_section_header(
        num_str="07",
        title="End-to-End Technical Request Lifecycle",
        summary="Comprehensive step-by-step trace of a user query across 15 discrete system operations.",
        sec_id="sec-07"
    ))

    html_out.append(b.build_diagram_box(
        fig_num="J",
        title="Fifteen-Step Technical Request Lifecycle Sequence",
        svg_name="diagram_j_request_lifecycle.svg",
        what="Sequential trace of execution beginning at ChatInput.jsx submission, passing through FastAPI, Redis, vector search, LLM completion, and rendering in ChatMessage.jsx.",
        how="Steps 1–5 handle client dispatch, API routing, and cache checking. Steps 6–10 execute query embedding, ChromaDB search, and prompt generation. Steps 11–15 deduplicate citations, update Redis cache, append to localStorage, and render in UI.",
        why="Provides a predictable, auditable sequence where each stage has explicit timeout and exception boundaries.",
        interview_point="Citations are deduplicated at Step 11 prior to caching at Step 12, ensuring cached responses include pre-computed, clean citations."
    ))

    # Section 08: Project Folder Structure & File Breakdown
    html_out.append(b.build_section_header(
        num_str="08",
        title="Complete Project Folder Structure & File Breakdown",
        summary="Authoritative mapping of repository directories, backend packages, frontend components, and configuration files.",
        sec_id="sec-08"
    ))

    html_out.append("""
    <div class="content-block">
      <pre><code>NexusRag/
├── backend/
│   ├── app/
│   │   ├── api/                 # HTTP Routes &amp; Dependency Injection
│   │   │   ├── dependencies.py  # FastAPI DI container (@lru_cache singletons)
│   │   │   ├── routes_chat.py   # POST /api/v1/chat endpoint
│   │   │   ├── routes_documents.py # Upload, list, replace, delete endpoints
│   │   │   └── routes_health.py # GET /api/v1/health endpoint
│   │   ├── cache/               # Distributed Query Caching
│   │   │   └── redis_cache.py   # RedisQueryCache wrapper (fail-open logic)
│   │   ├── chunking/            # Text Splitting Strategy
│   │   │   └── chunker.py       # RecursiveCharacterTextSplitter (800/100)
│   │   ├── core/                # Core Configuration &amp; Logging
│   │   │   ├── config.py        # Pydantic BaseSettings &amp; config.yaml loader
│   │   │   └── logging.py       # SensitiveDataFilter (API key redaction)
│   │   ├── embeddings/          # Vector Representation
│   │   │   └── embedder.py      # Google Gemini Embedding 2 wrapper
│   │   ├── ingestion/           # Document Ingestion Pipeline
│   │   │   ├── document_service.py # Document CRUD &amp; Safe Replacement
│   │   │   ├── loader.py        # PyPDFLoader &amp; TextLoader wrappers
│   │   │   └── pipeline.py      # Ingestion pipeline coordinator
│   │   ├── llm/                 # LLM Generation Gateway
│   │   │   ├── llm_service.py   # Abstract LLM interface
│   │   │   └── openrouter.py    # OpenRouter API client (Gemini 2.5 Flash)
│   │   ├── models/              # Pydantic Data Contracts
│   │   │   ├── requests.py      # ChatRequest, DocumentUpload schemas
│   │   │   └── responses.py     # RAGResponse, DocumentSummary, HealthResponse
│   │   ├── prompts/             # Prompt Engineering Templates
│   │   │   └── templates.py     # Grounded QA prompt template
│   │   ├── rag/                 # RAG Orchestration Domain
│   │   │   └── pipeline.py      # RAGPipeline (orchestrates cache, search, LLM)
│   │   ├── retrieval/           # Dense Similarity Search
│   │   │   └── retriever.py     # Retriever (embed query, search ChromaDB)
│   │   ├── utils/               # Sanitization &amp; Text Cleaners
│   │   │   └── helpers.py       # clean_text, sanitize_filename
│   │   ├── vectordb/            # Vector Database Abstraction
│   │   │   └── chroma_store.py  # ChromaStore (PersistentClient wrapper)
│   │   └── main.py              # FastAPI application entrypoint &amp; lifespan
│   ├── config.yaml              # Non-secret application configuration
│   ├── .env                     # Secret environment variables (API keys)
│   └── tests/                   # 184 Backend Pytest Unit &amp; Integration Tests
└── frontend/
    ├── src/
    │   ├── components/          # Reusable UI Components (Navbar, ChatInput, ...)
    │   ├── context/             # ConversationContext (localStorage persistence)
    │   ├── hooks/               # Custom hooks (useChat.js)
    │   ├── pages/               # ChatPage.jsx, DocumentsPage.jsx
    │   ├── services/            # api.js (Fetch HTTP client)
    │   └── App.jsx              # React router &amp; provider tree
    └── src/__tests__/           # 52 Frontend Vitest Unit &amp; Integration Tests</code></pre>

      <h3>8.1 Component Responsibilities Matrix</h3>
      <table>
        <thead>
          <tr>
            <th>Module / File</th>
            <th>Primary Architectural Responsibility</th>
            <th>Critical Design Invariant</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>backend/app/rag/pipeline.py</code></td>
            <td>Orchestrates cache check, query embedding, vector search, prompt grounding, and LLM call.</td>
            <td>Must fail-open if Redis is unreachable; returns deterministic refusal if context is empty.</td>
          </tr>
          <tr>
            <td><code>backend/app/cache/redis_cache.py</code></td>
            <td>Stores and retrieves serialized RAG responses using SHA-256 normalized query hashes.</td>
            <td>Wraps all socket operations in try/except; increments error metric and returns None on exception.</td>
          </tr>
          <tr>
            <td><code>backend/app/vectordb/chroma_store.py</code></td>
            <td>Wraps ChromaDB PersistentClient; handles collection initialization, indexing, and deletes.</td>
            <td>Computes physical chunk counts dynamically from stored records rather than trusting metadata.</td>
          </tr>
          <tr>
            <td><code>backend/app/ingestion/document_service.py</code></td>
            <td>Manages document lifecycle: staging, format detection, chunking, embedding, and deletion.</td>
            <td>Implements atomic-like replacement: embeds new document before deleting old vectors.</td>
          </tr>
          <tr>
            <td><code>frontend/src/context/ConversationContext.jsx</code></td>
            <td>Maintains multi-turn chat message history and active conversation state.</td>
            <td>Syncs changes to localStorage key <code>nexusrag:chat-history:v1</code> on every message append.</td>
          </tr>
        </tbody>
      </table>
    </div>
    """)

    return "".join(html_out)

print("Part II generator ready.")
