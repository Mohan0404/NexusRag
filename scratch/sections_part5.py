"""
Part V Generator for NexusRAG Handbook: FastAPI, Concurrency, CRUD, React, and Code Analysis.
"""

def generate_part_5(builder):
    b = builder
    html_out = []

    # Part V Divider
    topics = [
        {"title": "22. FastAPI Concurrency & Async I/O Model", "desc": "Asyncio event loops, thread pool delegation for sync tasks, and Uvicorn workers."},
        {"title": "23. Dependency Injection Architecture", "desc": "Explicit provider pattern using dependencies.py, @lru_cache, and test overrides."},
        {"title": "24. Error Handling & Exception Hierarchy", "desc": "Custom domain exceptions mapped to clean HTTP status codes."},
        {"title": "25. Document CRUD Lifecycle (Figure F)", "desc": "Four-quadrant management of Create, Read, Update, and Delete operations."},
        {"title": "26. Safe Document Replacement (Figure G)", "desc": "Atomic-like replacement protocol guaranteeing zero data loss on embedding failure."},
        {"title": "27. Frontend Architecture & Context", "desc": "React 18 SPA, Vite, ConversationContext, and custom hook useChat."},
        {"title": "28. Chat History Persistence", "desc": "Client-side localStorage architecture with key nexusrag:chat-history:v1."},
        {"title": "29. Critical Code Snippets & Analysis", "desc": "Deep implementation review of pipeline, retriever, cache, and replacement code."}
    ]
    html_out.append(b.build_part_divider(
        roman="V",
        title="ENGINEERING DEEP DIVE",
        quote="Low-level implementation details: async concurrency, dependency injection, atomic document replacement, and state persistence.",
        topics=topics
    ))

    # Section 22: FastAPI Backend Architecture & Concurrency
    html_out.append(b.build_section_header(
        num_str="22",
        title="FastAPI Backend Architecture & Concurrency Model",
        summary="Asynchronous event loop mechanics, non-blocking I/O execution, and thread pool worker delegation.",
        sec_id="sec-22"
    ))

    html_out.append("""
    <div class="content-block">
      <h3>22.1 Asynchronous Event Loop vs Blocking Operations</h3>
      <p>
        FastAPI runs on Uvicorn ASGI using Python's standard <code>asyncio</code> event loop. Because Python's event loop is single-threaded, executing a CPU-intensive operation or a blocking synchronous network/disk call inside an <code>async def</code> route halts all concurrent request processing.
      </p>
      <p>
        In NexusRAG, operations are categorized by concurrency behavior:
      </p>
      <ul>
        <li><strong>Non-blocking I/O (Async):</strong> HTTP request parsing, Pydantic validation, Redis non-blocking network calls, and async HTTP requests.</li>
        <li><strong>Synchronous Blocking Workloads:</strong> ChromaDB SQLite disk writes, PyPDFLoader text extraction, and LangChain splitter loops.</li>
      </ul>
      <p>
        To prevent blocking the event loop during heavy document ingestion, FastAPI automatically offloads synchronous route handler functions (defined with standard <code>def</code> instead of <code>async def</code>) to an internal AnyIO worker thread pool.
      </p>

      <div class="callout callout-tip no-break">
        <div class="callout-header"><span>💡</span> INTERVIEW POINT: ASYNC DEF VS DEF IN FASTAPI</div>
        <p>
          "In FastAPI, defining a route as <code>async def</code> means FastAPI executes it directly on the main event loop. If that route calls a synchronous library like PyPDFLoader, it will freeze the server for all other users! By defining synchronous routes with standard <code>def</code>, FastAPI automatically schedules them on separate worker threads from a thread pool, keeping the main event loop responsive."
        </p>
      </div>
    </div>
    """)

    # Section 23: Dependency Injection Architecture
    html_out.append(b.build_section_header(
        num_str="23",
        title="Dependency Injection Architecture (`dependencies.py`)",
        summary="Explicit provider pattern utilizing FastAPI's Depends() container and Python's @lru_cache for singletons.",
        sec_id="sec-23"
    ))

    html_out.append("""
    <div class="content-block">
      <p>
        Rather than creating global module-level instances of database connections or AI services, NexusRAG consolidates all factory functions in <code>backend/app/api/dependencies.py</code>:
      </p>
      <pre><code>@lru_cache()
def get_settings() -> Settings:
    return Settings()

@lru_cache()
def get_chroma_store(settings: Settings = Depends(get_settings)) -> ChromaStore:
    return ChromaStore(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.vectordb.collection_name
    )

def get_rag_pipeline(
    retriever: Retriever = Depends(get_retriever),
    llm: LLMService = Depends(get_llm_service),
    cache: RedisQueryCache = Depends(get_redis_cache)
) -> RAGPipeline:
    return RAGPipeline(retriever=retriever, llm_service=llm, cache=cache)</code></pre>
      <p>
        This architecture delivers two immense engineering benefits:
      </p>
      <ol>
        <li><strong>Singleton Lifecycle:</strong> <code>@lru_cache()</code> guarantees that heavy objects (like ChromaDB clients and Redis pools) are instantiated only once per server worker.</li>
        <li><strong>Trivial Testing Overrides:</strong> In pytest, tests swap out real services for mocks with a single line: <code>app.dependency_overrides[get_redis_cache] = lambda: mock_cache</code>.</li>
      </ol>
    </div>
    """)

    # Section 24: Error Handling & Exception Hierarchy
    html_out.append(b.build_section_header(
        num_str="24",
        title="Error Handling & Custom Exception Hierarchy",
        summary="Domain-driven exception classes mapped to standardized HTTP status codes with sanitization filters.",
        sec_id="sec-24"
    ))

    html_out.append("""
    <div class="content-block">
      <pre><code>class NexusRAGException(Exception):
    \"\"\"Base exception for all NexusRAG domain errors.\"\"\"

class IngestionError(NexusRAGException):
    \"\"\"Raised during document parsing, chunking, or file staging.\"\"\"

class EmbeddingProviderError(NexusRAGException):
    \"\"\"Raised when Gemini Embedding API fails, times out, or exceeds quota.\"\"\"

class LLMProviderError(NexusRAGException):
    \"\"\"Raised when OpenRouter LLM gateway fails or returns 5xx.\"\"\"

class VectorStoreError(NexusRAGException):
    \"\"\"Raised when ChromaDB suffers disk I/O or SQLite lock failure.\"\"\"</code></pre>

      <h3>24.1 HTTP Status Code Mapping Matrix</h3>
      <table>
        <thead>
          <tr>
            <th>Exception Class</th>
            <th>Trigger Condition</th>
            <th>HTTP Status</th>
            <th>Client Error Payload</th>
          </tr>
        </thead>
        <tbody>
          <tr><td><code>ValueError</code> / <code>ValidationError</code></td><td>Malformed JSON query or invalid file extension</td><td><strong>400 Bad Request</strong></td><td><code>{"detail": "Invalid file extension. Allowed: .pdf, .txt, .md"}</code></td></tr>
          <tr><td><code>DocumentNotFoundError</code></td><td>Replace or delete target document does not exist</td><td><strong>404 Not Found</strong></td><td><code>{"detail": "Document 'policy.pdf' not found."}</code></td></tr>
          <tr><td><code>FileTooLargeError</code></td><td>Upload exceeds 10 MB limit</td><td><strong>413 Payload Too Large</strong></td><td><code>{"detail": "File size exceeds 10 MB maximum limit."}</code></td></tr>
          <tr><td><code>IngestionError</code></td><td>Corrupt PDF or zero extractable text content</td><td><strong>422 Unprocessable</strong></td><td><code>{"detail": "No extractable text found in uploaded document."}</code></td></tr>
          <tr><td><code>EmbeddingProviderError</code></td><td>Gemini embedding rate limit (429) or timeout</td><td><strong>502 Bad Gateway</strong></td><td><code>{"detail": "Embedding provider temporarily unavailable."}</code></td></tr>
          <tr><td><code>LLMProviderError</code></td><td>OpenRouter 5xx error after 3 retries</td><td><strong>502 Bad Gateway</strong></td><td><code>{"detail": "Upstream LLM reasoning gateway unavailable."}</code></td></tr>
        </tbody>
      </table>
    </div>
    """)

    # Section 25: Document CRUD Lifecycle (Figure F)
    html_out.append(b.build_section_header(
        num_str="25",
        title="Document Lifecycle Management (CRUD Operations)",
        summary="Four-quadrant operations ensuring bidirectional synchronization between disk files, vector indexes, and caches.",
        sec_id="sec-25"
    ))

    html_out.append(b.build_diagram_box(
        fig_num="F",
        title="Document CRUD Lifecycle Operations Grid",
        svg_name="diagram_f_document_crud.svg",
        what="Comprehensive four-quadrant layout detailing CREATE (Upload), READ (List), UPDATE (Safe Replace), and DELETE (Purge) operations.",
        how="CREATE stages, splits, embeds, indexes, and purges cache. READ queries ChromaDB and calculates physical chunk totals. UPDATE stages new, indexes, and on success purges old vectors. DELETE removes vectors by source filter and purges Redis.",
        why="Document modifications must immediately synchronize with vector storage and clear cache to prevent stale answers.",
        interview_point="Listing documents computes counts directly from physical records in ChromaDB rather than trusting cached metadata tags, preventing UI drift."
    ))

    # Section 26: Safe Document Replacement (Figure G)
    html_out.append(b.build_section_header(
        num_str="26",
        title="Safe Document Replacement Protocol (Zero Data Loss)",
        summary="Atomic-like replacement algorithm indexing new files before deleting old vectors to prevent knowledge corruption.",
        sec_id="sec-26"
    ))

    html_out.append(b.build_diagram_box(
        fig_num="G",
        title="Safe Document Replacement Flow & Failure Rollback",
        svg_name="diagram_g_safe_replacement.svg",
        what="Decision flow demonstrating the 'Index First, Delete Second' replacement guarantee in routes_documents.py.",
        how="When a user replaces an existing file, the new file is staged and indexed into ChromaDB FIRST. If indexing fails at any point, the old document's vectors are left untouched, ensuring zero data loss. Only upon verified success are old vectors deleted.",
        why="Naive replacement deletes old vectors first. If the network drops or the embedding API fails during indexing, the document is permanently destroyed.",
        interview_point="If replacement fails halfway, the system guarantees 100% data preservation and zero downtime for the existing document."
    ))

    # Section 27: Frontend Architecture & Context
    html_out.append(b.build_section_header(
        num_str="27",
        title="Frontend Architecture (React 18 + Vite + Custom Context)",
        summary="Decoupled single-page application utilizing React Router v6, custom hook useChat, and ConversationContext.",
        sec_id="sec-27"
    ))

    html_out.append("""
    <div class="content-block">
      <h3>27.1 Component Hierarchy</h3>
      <p>
        The frontend is built as a lightweight, high-performance client SPA without server-side rendering overhead:
      </p>
      <ul>
        <li><code>App.jsx</code>: Top-level provider wrapper enclosing <code>BrowserRouter</code> and <code>ConversationProvider</code>.</li>
        <li><code>Navbar.jsx</code>: Navigation header with route tabs (<code>/chat</code>, <code>/documents</code>) and "+ New Chat" button.</li>
        <li><code>ChatPage.jsx</code>: Message stream container rendering <code>ChatMessage</code> components and sticky <code>ChatInput</code>.</li>
        <li><code>DocumentsPage.jsx</code>: Document inventory table, upload dropzone, replacement modal, and deletion confirmation modal.</li>
        <li><code>useChat.js</code>: Custom hook managing loading states, error banners, message appending, and API dispatch.</li>
      </ul>
    </div>
    """)

    # Section 28: Chat History localStorage Persistence
    html_out.append(b.build_section_header(
        num_str="28",
        title="State Management & Client-Side Conversation Persistence",
        summary="Decentralized conversation storage backed by browser localStorage under key `nexusrag:chat-history:v1`.",
        sec_id="sec-28"
    ))

    html_out.append("""
    <div class="content-block">
      <p>
        To provide seamless multi-turn conversation continuity without the operational complexity of managing user accounts and database sessions, NexusRAG stores chat history in the browser:
      </p>
      <pre><code>// localStorage key schema
const STORAGE_KEY = 'nexusrag:chat-history:v1';

// Synchronized state update inside ConversationProvider
useEffect(() => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  } catch (err) {
    console.warn('Failed to persist chat messages to localStorage', err);
  }
}, [messages]);</code></pre>
      <div class="callout callout-info no-break">
        <div class="callout-header"><span>ℹ️</span> MULTI-TURN PERSISTENCE GUARANTEES</div>
        <p>
          Users can freely navigate between the Chat page and the Documents page, upload new documents, and return to Chat with zero conversation loss. Even hard browser tab refreshes preserve the complete question-and-answer stream with full source citation badges.
        </p>
      </div>
    </div>
    """)

    # Section 29: Critical Code Snippets & Implementation Analysis
    html_out.append(b.build_section_header(
        num_str="29",
        title="Critical Code Snippets & Implementation Analysis",
        summary="Four critical backend snippets demonstrating fail-open caching, safe replacement, vector retrieval, and pipeline orchestration.",
        sec_id="sec-29"
    ))

    # Snippet 1: Redis Fail-Open
    html_out.append(b.build_code_card(
        filepath="backend/app/cache/redis_cache.py",
        function_name="get",
        purpose="Fail-open distributed query cache lookup returning None on socket exceptions",
        code_snippet="""def get(self, key: str) -> Optional[Any]:
    if self._client is None:
        self._metrics.misses += 1
        return None

    start_time = time.perf_counter()
    try:
        raw_data = self._client.get(key)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if raw_data is None:
            self._metrics.misses += 1
            self._metrics.total_miss_latency_ms += latency_ms
            return None

        response = deserialize_rag_response(raw_data)
        if response is None:
            self._metrics.misses += 1
            self._metrics.total_miss_latency_ms += latency_ms
            return None

        self._metrics.hits += 1
        self._metrics.total_hit_latency_ms += latency_ms
        return response
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        self._metrics.errors += 1
        self._metrics.misses += 1
        self._metrics.total_miss_latency_ms += latency_ms
        logger.warning("Redis GET failed (fail-open to RAG pipeline): %s", exc)
        return None""",
        interview_q="What happens if Redis crashes or encounters a network partition during a query?",
        why_answer="The entire operation is wrapped in try/except. Any socket error increments the error metric, treats the query as a cache miss, and falls open to the RAG pipeline without failing the user's request."
    ))

    # Snippet 2: Safe Document Replacement
    html_out.append(b.build_code_card(
        filepath="backend/app/api/routes_documents.py",
        function_name="replace_document",
        purpose="Safe document replacement: stages and indexes new file before purging old vectors",
        code_snippet="""# Step 1: Verify target document exists in vector store
existing_docs = chroma_store.list_sources()
if not any(d["source"] == filename for d in existing_docs):
    raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")

# Step 2: Stage new file to isolated UUID path
staged_path = await stage_upload_file(file)

try:
    # Step 3: Ingest, chunk, and embed new file FIRST
    new_chunks = doc_service.ingest_file(staged_path, canonical_filename=filename)
    
    # Step 4: On verified success, delete old vectors
    chroma_store.delete_by_source(filename, exclude_new_ids=[c.id for c in new_chunks])
    
    # Step 5: Invalidate entire Redis query cache
    redis_cache.clear()
    return {"status": "replaced", "chunks_indexed": len(new_chunks)}
except Exception as exc:
    # ROLLBACK: Do NOT delete old vectors!
    logger.error("Replacement failed; keeping existing vectors intact: %s", exc)
    raise HTTPException(status_code=502, detail="Failed to index replacement file.")
finally:
    if os.path.exists(staged_path):
        os.unlink(staged_path)""",
        interview_q="How does NexusRAG guarantee zero downtime and zero data loss during document replacement?",
        why_answer="By strictly executing ingestion and embedding before deletion. If the embedding API times out, the exception is caught, the old vectors are left intact, and the system continues answering questions from the existing document."
    ))

    # Snippet 3: RAGPipeline.query()
    html_out.append(b.build_code_card(
        filepath="backend/app/rag/pipeline.py",
        function_name="query",
        purpose="Orchestrates query normalization, cache checking, vector retrieval, and prompt injection",
        code_snippet="""def query(self, question: str) -> RAGResponse:
    norm_query = question.strip().lower()
    cache_key = self.cache.generate_key(norm_query)

    # 1. Check Redis Cache
    cached = self.cache.get(cache_key)
    if cached is not None:
        return cached

    # 2. Retrieve Top-K relevant chunks
    chunks = self.retriever.retrieve(norm_query)

    # 3. Empty context guard
    if not chunks:
        return RAGResponse(
            answer="I could not find any relevant information in the uploaded documents.",
            sources=[],
            latency_ms=elapsed_ms,
            model=self.config.model
        )

    # 4. Construct grounded prompt & call LLM
    prompt = self._build_prompt(norm_query, chunks)
    raw_answer = self.llm.generate(prompt)

    # 5. Extract deduplicated citations & cache response
    citations = self._deduplicate_sources(chunks)
    response = RAGResponse(answer=raw_answer, sources=citations, latency_ms=elapsed_ms)
    self.cache.set(cache_key, response)
    return response""",
        interview_q="Why does the RAG pipeline perform query normalization before cache lookup?",
        why_answer="Normalizing whitespace and casing ensures that 'What is policy?' and 'what is policy? ' map to the exact same cache key, maximizing cache hit ratio and preventing duplicate LLM spend."
    ))

    return "".join(html_out)

print("Part V generator ready.")
