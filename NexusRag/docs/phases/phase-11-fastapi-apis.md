# Phase 11 — FastAPI API Layer

## 1. Objective

Implement a production-grade FastAPI HTTP API layer around the Genworx Knowledge Assistant (`NexusRAG`).

Phase 11 exposes the underlying RAG pipeline and document ingestion system via standard, performant RESTful HTTP endpoints without embedding domain logic, retrieval algorithms, prompt construction, LLM generation, or database operations directly inside route handlers. FastAPI functions purely as an HTTP adapter, protocol validator, and dependency injection orchestrator.

### Exposed Endpoints:
- `GET  /api/v1/health`: Lightweight liveness probe returning application health status.
- `POST /api/v1/chat`: Natural language question-answering endpoint delegating to `RAGPipeline.query()`.
- `POST /api/v1/documents/upload`: Streaming multipart document ingestion endpoint delegating to `IngestionPipeline.index_file()` and invalidating the Redis query cache.

---

## 2. Architecture

```text
                                HTTP Clients
                        (Browser / Frontend / cURL)
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
        POST /api/v1/chat                      POST /api/v1/documents/upload
                 │                                       │
                 ▼                                       ▼
       [Pydantic Validation]                  [Streaming File Upload]
        (ChatRequest model)                   (Sanitize, 10MB limit, staging)
                 │                                       │
                 ▼                                       ▼
       [FastAPI Dependencies]                 [FastAPI Dependencies]
        (get_rag_pipeline)                    (get_ingestion_pipeline)
                 │                                       │
                 ▼                                       ▼
       [RAGPipeline.query()]             [run_in_threadpool(IngestionPipeline)]
                 │                                       │
        ┌────────┴────────┐                              ├── DocumentService.ingest_file()
        │                 │                              ├── DocumentChunker.chunk_documents()
   [Cache Hit]       [Cache Miss]                        ├── GeminiEmbeddingService.embed_documents()
   (Redis Fast)    (ChromaDB + LLM)                      ├── ChromaStore.add_embedded_chunks()
        │                 │                              │
        └────────┬────────┘                              ▼
                 │                               [Cache Invalidation]
                 ▼                               (RedisQueryCache.clear())
        [RAGResponse Dataclass]                          │
                 │                                       ▼
                 ▼                              [IngestionResult]
        [ChatResponse Model]                             │
                 │                                       ▼
                 ▼                          [DocumentUploadResponse Model]
            HTTP 200 OK                              HTTP 200 OK
```

---

## 3. API Endpoints

### 3.1 Health Check (`GET /api/v1/health`)
- **Method**: `GET`
- **Path**: `/api/v1/health`
- **Tags**: `["Health"]`
- **Purpose**: Fast, dependency-free liveness probe for load balancers and container orchestrators (e.g. Kubernetes, AWS ECS).
- **External Dependencies**: Zero. It does not ping Gemini, OpenRouter, ChromaDB, or Redis, ensuring liveness remains decoupled from transient upstream degradation.
- **Status Code**: `200 OK`
- **Response**:
```json
{
  "status": "healthy"
}
```

### 3.2 Chat Query (`POST /api/v1/chat`)
- **Method**: `POST`
- **Path**: `/api/v1/chat`
- **Tags**: `["Chat"]`
- **Purpose**: Submits a user question to the RAG pipeline for retrieval-augmented generation.
- **Request Content-Type**: `application/json`
- **Status Codes**:
  - `200 OK`: Successful answer or controlled no-context answer.
  - `422 Unprocessable Entity`: Validation failure (empty, whitespace-only, missing, or > 2000 characters).
  - `500 Internal Server Error`: Vector database or retrieval failure (`RetrievalError`).
  - `502 Bad Gateway`: LLM provider outage, rate-limit exhaustion, or upstream API error (`LLMProviderError`).

### 3.3 Document Upload (`POST /api/v1/documents/upload`)
- **Method**: `POST`
- **Path**: `/api/v1/documents/upload`
- **Tags**: `["Documents"]`
- **Purpose**: Securely uploads and indexes an enterprise document into ChromaDB and clears stale query caches.
- **Request Content-Type**: `multipart/form-data`
- **Allowed Formats**: `.pdf`, `.txt`, `.md`
- **Size Limit**: 10 MB (enforced on stream)
- **Status Codes**:
  - `200 OK`: Successful ingestion, embedding, vector indexing, and cache invalidation.
  - `400 Bad Request`: Blank filename, missing file, unsupported file extension, or 0-byte file.
  - `413 Request Entity Too Large`: File exceeds configured maximum size.
  - `422 Unprocessable Entity`: Corrupted file or document with no extractable text.
  - `500 Internal Server Error`: Ingestion pipeline failure or ChromaDB persistence error.

---

## 4. Request/Response Schemas

All API models are implemented using Pydantic v2 in `app/models/requests.py` and `app/models/responses.py`. Domain dataclasses (`RAGResponse`, `SourceReference`, `Document`, `EmbeddedChunk`) are kept separate from external HTTP contracts.

### 4.1 `ChatRequest`
```python
class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question to be answered by the RAG assistant",
        examples=["What is the annual leave policy?"],
    )

    @field_validator("question", mode="before")
    @classmethod
    def strip_and_validate_whitespace(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Question cannot be empty or contain only whitespace.")
        return v
```

### 4.2 `SourceResponse`
```python
class SourceResponse(BaseModel):
    source: str = Field(..., description="Filename of the source document")
    file_type: str = Field(default="", description="Extension / format of the document")
    page: int = Field(default=1, description="1-indexed page number from the original file")
```

### 4.3 `ChatResponse`
```python
class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded answer text generated by the LLM")
    sources: List[SourceResponse] = Field(default_factory=list, description="Deduplicated citations")
    query: str = Field(..., description="The user question, preserved verbatim")
    model: str = Field(default="", description="LLM model identifier used for generation")
    context_chunks_used: int = Field(default=0, description="Number of context chunks used")
```

### 4.4 `DocumentUploadResponse`
```python
class DocumentUploadResponse(BaseModel):
    filename: str = Field(..., description="Sanitized original filename")
    file_type: str = Field(..., description="Detected file extension")
    file_size_bytes: int = Field(..., description="Total size of the file in bytes")
    chunks_created: int = Field(..., description="Number of text chunks created and indexed")
    status: str = Field(default="success", description="Ingestion status string ('success')")
    message: str = Field(..., description="Human-readable result summary")
```

---

## 5. Dependency Injection

FastAPI's dependency injection system (`backend/app/api/dependencies.py`) wires together components.

### Shared Infrastructure Services:
1. `get_settings()`: Cached application configuration via `@lru_cache`.
2. `get_embedding_service()`: Cached `GeminiEmbeddingService` singleton.
3. `get_chroma_store()`: Cached `ChromaStore` persistent vector store singleton.
4. `get_llm_service()`: Cached `OpenRouterLLMService` client singleton.
5. `get_query_cache()`: Cached `RedisQueryCache` instance connecting to Redis.

### Pipeline Orchestrators:
6. `get_retriever()`: Creates `Retriever` wired to `get_embedding_service()` and `get_chroma_store()`.
7. `get_rag_pipeline()`: Creates `RAGPipeline` wired to `get_retriever()`, `get_llm_service()`, and `get_query_cache()`.
8. `get_ingestion_pipeline()`: Creates `IngestionPipeline` wired to `DocumentService`, `DocumentChunker`, `GeminiEmbeddingService`, `ChromaStore`, and `RedisQueryCache`.

### Testability:
In unit and integration tests, all underlying clients are swapped cleanly using `app.dependency_overrides`:
```python
app.dependency_overrides[get_rag_pipeline] = lambda: mock_pipeline
app.dependency_overrides[get_ingestion_pipeline] = lambda: mock_ingestion
```

---

## 6. Application Lifecycle

Managed in `backend/app/main.py` via FastAPI's `lifespan` context manager:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: configure logging and log environment details
    setup_logging()
    logger.info("Starting NexusRAG (v%s) in [%s] environment", settings.VERSION, settings.ENVIRONMENT)
    yield
    # Shutdown: clean resource release
    logger.info("Shutting down NexusRAG")
```
Infrastructure connections (ChromaDB PersistentClient, Redis connection pools, OpenRouter HTTP sessions) are lazily evaluated or pool-managed without blocking application startup.

---

## 7. Chat Flow

When `POST /api/v1/chat` is invoked:
1. **Pydantic Validation**: `ChatRequest` strips whitespace, checks `1 <= len <= 2000`, and rejects invalid payloads with HTTP 422.
2. **Dependency Resolution**: Injects the configured `RAGPipeline` instance.
3. **Execution**: Calls `rag_pipeline.query(request.question)`.
   - Checks Redis cache (returns immediately on cache hit).
   - On miss: retrieves chunks from ChromaDB via dense embeddings.
   - If empty chunks: returns `NO_CONTEXT_ANSWER` (HTTP 200).
   - If chunks exist: constructs grounded prompt and calls LLM.
   - Stores successful result in Redis with TTL.
4. **Mapping**: Converts domain `RAGResponse` to API `ChatResponse`.
5. **Exception Handling**:
   - `LLMProviderError` maps to HTTP 502 Bad Gateway.
   - `RetrievalError` maps to HTTP 500 Internal Server Error.

---

## 8. Document Upload Flow

When `POST /api/v1/documents/upload` is invoked:
1. **Filename Sanitization**: Rejects blank or empty filenames (HTTP 400). Sanitizes path using `Path(raw_filename).name`.
2. **Extension Allowlist**: Verifies extension against `settings.allowed_extensions` (`.pdf`, `.txt`, `.md`). Rejects unknown types with HTTP 400.
3. **Secure Staging**: Assigns a UUID prefix (`{uuid.hex}_{sanitized_name}`) to prevent collisions and path traversal in `data/uploads`.
4. **Streaming & Size Limit**: Streams file in 64 KB chunks. If cumulative bytes exceed `max_file_size_bytes` (10 MB), stream is terminated, partial staging file is deleted, and HTTP 413 is returned.
5. **Zero-Byte Check**: If cumulative bytes == 0, removes staging file and returns HTTP 400.
6. **Threadpool Dispatch**: Invokes `run_in_threadpool(ingestion_pipeline.index_file, staged_path)` to prevent blocking the async event loop during CPU/IO-heavy parsing and embedding.
7. **Ingestion Pipeline**:
   - `DocumentService.ingest_file()` parses document.
   - `DocumentChunker.chunk_documents()` splits text into sliding windows.
   - `GeminiEmbeddingService.embed_documents()` generates dense vector embeddings.
   - `ChromaStore.add_embedded_chunks()` stores vectors and metadata in ChromaDB.
8. **Cache Invalidation**: Triggers `RedisQueryCache.clear()`.
9. **Cleanup & Response**: Closes file handle, constructs `DocumentUploadResponse` with chunks count and byte size.

---

## 9. Cache Invalidation

Implemented according to Phase 11 Correction #2:
- **Hook Location**: Executed inside `IngestionPipeline.index_file()` immediately following successful `ChromaStore.add_embedded_chunks()`.
- **Global Scope**: Phase 11 invalidates the global query cache namespace (`nexusrag:query:v1:*`) because the knowledge base is shared across all queries.
- **Conditional Trigger**:
  - Cache is **ONLY** invalidated upon successful document indexing.
  - If document parsing, chunking, embedding, or vector storage raises an error, cache invalidation is completely skipped.
- **Fail-Open Resilience**:
  - If `RedisQueryCache.clear()` raises a connection or timeout error, the exception is caught, a warning is logged, and ingestion remains successful (`cache_cleared=False`). Redis is an optimization layer; an invalidation failure does not invalidate stored document vectors.

---

## 10. Error Handling

Errors are mapped to standard HTTP status codes without leaking internal stack traces, API keys, or server paths:

| Exception Type | HTTP Status Code | Description |
|---|---|---|
| `pydantic.ValidationError` | 422 Unprocessable Entity | Invalid request JSON, whitespace query, missing fields |
| `UnsupportedFileTypeError` | 400 Bad Request | File extension not in allowlist |
| `EmptyFileError` / 0-byte stream | 400 Bad Request | Uploaded file contains zero bytes |
| Empty / blank filename | 400 Bad Request | Filename was blank or composed only of spaces |
| `FileTooLargeError` / stream overflow | 413 Payload Too Large | File exceeds 10 MB limit |
| `CorruptedFileError` / `EmptyContentError` | 422 Unprocessable Entity | Unreadable PDF or document with no extractable text |
| `RetrievalError` / `VectorStoreError` | 500 Internal Server Error | Vector DB failure or embedding generation error |
| `LLMProviderError` | 502 Bad Gateway | Upstream LLM provider outage, rate limits, or network timeout |
| Unexpected Python exceptions | 500 Internal Server Error | Generic error message; full traceback logged server-side only |

---

## 11. Upload Security

1. **Path Traversal Defense**: All filenames pass through `Path(raw_filename).name` and `.strip()`. Characters like `../`, `..\\`, or absolute paths (`/etc/passwd`) are stripped to base names.
2. **UUID Staging Isolation**: Files are written to `data/uploads/{uuid}_{basename}`, preventing filename collisions, race conditions, or overwriting existing documents.
3. **Extension Allowlist**: Strict check against `[".pdf", ".txt", ".md"]`. Executables, scripts (`.py`, `.sh`, `.bat`), and HTML files are rejected before saving.
4. **Streaming Memory Protection**: Files are read in 64 KB buffers rather than loaded into RAM in one chunk, preventing memory exhaustion (DoS attacks).
5. **Partial File Removal**: Staged files are removed immediately if a stream exceeds size bounds or fails validation.
6. **No Internal Path Disclosure**: API responses contain only sanitized original filenames and chunk counts; filesystem paths are never returned to clients.

---

## 12. Sync vs Async Decision

- **`GET /api/v1/health`**: Implemented with `async def` since it performs a trivial non-blocking dictionary return.
- **`POST /api/v1/chat`**: Implemented with normal `def`. The underlying `RAGPipeline.query()` is synchronous (standard HTTP client for OpenRouter, vector search in ChromaDB, Redis queries). Using `def` directs FastAPI to execute the route in an AnyIO worker threadpool, preventing blocking of the main event loop.
- **`POST /api/v1/documents/upload`**: Implemented with `async def` to allow asynchronous streaming of multipart chunks (`await file.read(64 * 1024)`). However, the synchronous ingestion pipeline execution is offloaded via `await run_in_threadpool(ingestion_pipeline.index_file, staged_path)`.

---

## 13. Testing Strategy

Tests are separated into three dedicated modules under `backend/tests/`:
1. `backend/tests/test_health.py`: Liveness tests verifying 200 OK without external services (3 tests).
2. `backend/tests/test_chat.py`: Chat endpoint tests covering Pydantic validation, delegation, error mappings, and citations (10 tests).
3. `backend/tests/test_documents.py`: Document upload endpoint tests covering streaming limits, sanitization, extension allowlists, and cache invalidation (12 tests).

All unit tests use `fastapi.testclient.TestClient` and mock dependencies (`MagicMock`) to guarantee zero calls to external APIs (Gemini, OpenRouter, ChromaDB, or Redis).

---

## 14. OpenAPI

FastAPI's built-in OpenAPI engine automatically generates API specifications at:
- **Interactive Swagger UI**: `/api/v1/docs`
- **ReDoc UI**: `/api/v1/redoc`
- **Raw OpenAPI 3.1 JSON Schema**: `/api/v1/openapi.json`

All endpoints include descriptive summaries, operation descriptions, parameter documentation, and status code response mappings.

---

## 15. Design Decisions

1. **Thin Route Architecture**: Ingestion and RAG logic live in `IngestionPipeline` and `RAGPipeline`. Routes strictly handle HTTP requests, headers, file streaming, and status codes.
2. **Global Cache Invalidation**: As the knowledge base is currently shared and non-multitenant, adding documents invalidates the global namespace.
3. **Fail-Open Optimization**: Redis cache failures during invalidation or lookup never fail document uploads or chat requests.
4. **No Premature RFC 7807 Implementation**: Uses standard FastAPI JSON error payloads (`{"detail": "..."}`) rather than partial `application/problem+json` envelopes.

---

## 16. Limitations

1. **Synchronous Ingestion**: Document uploads are processed synchronously inside worker threads. Large files (e.g. 50-page PDFs) will hold the HTTP connection open until indexing completes.
2. **No Document Versioning / Granular Invalidation**: Cache invalidation flushes the entire query cache rather than selectively evicting queries affected by the newly uploaded document.
3. **No Authentication / Multi-Tenancy**: The API does not yet implement API keys, JWTs, or user namespaces.
4. **No Streaming Responses**: Chat answers are returned as monolithic JSON strings once generation finishes.

---

## 17. Future Improvements

1. **Background Tasks / Asynchronous Processing**: Offload document ingestion to Celery or RQ workers, returning an ingestion task ID for polling.
2. **Server-Sent Events (SSE) / Streaming**: Stream LLM tokens to the client in real-time as they are generated.
3. **Document-Aware Invalidation**: Tag cache entries with document IDs or semantic topics to evict only relevant cache entries upon new uploads.
4. **Authentication & Authorization**: Add JWT / OAuth2 security dependencies for protected endpoints.

---

## 18. Interview Questions & Answers

### Q1: Why should FastAPI route handlers be kept thin in a RAG architecture?
**A**: Keeping routes thin decouples HTTP transport concerns (status codes, headers, multipart streaming, JSON deserialization) from domain business logic (RAG query flow, chunking, embeddings, vector storage). This allows the core RAG pipeline and ingestion logic to be reused across different interfaces (e.g. CLI tools, background workers, RPC services) and drastically simplifies unit testing through dependency injection without spinning up HTTP servers.

### Q2: Why is `run_in_threadpool` used for document ingestion in an async route?
**A**: In Python's `asyncio` event loop, executing CPU-heavy tasks (PDF text extraction, chunking) or synchronous blocking I/O (local disk writes, blocking HTTP calls to embedding APIs) blocks the entire event loop. No other incoming requests can be received or processed during that time. `run_in_threadpool` offloads the synchronous function to Starlette's threadpool, keeping the event loop responsive to other concurrent requests.

### Q3: Why does `POST /chat` use standard `def` instead of `async def`?
**A**: FastAPI automatically runs standard `def` endpoint functions inside an AnyIO threadpool worker. Since `RAGPipeline.query()` calls synchronous database and API clients, defining the route as `async def` would block the event loop unless every single call inside it were made natively asynchronous. Defining it as `def` achieves concurrent threadpool execution with zero code changes to Phase 3–10 internals.

### Q4: Why is cache invalidation placed in `IngestionPipeline` rather than `routes_documents.py`?
**A**: If cache invalidation were placed inside the HTTP route, documents ingested via batch scripts, CLI tools, or background queues would fail to invalidate the query cache, causing stale answers to persist. Placing it in the application-level `IngestionPipeline` ensures that cache invalidation is consistently triggered whenever documents are added to ChromaDB, regardless of the entry point.

### Q5: How does the system defend against path traversal attacks during document upload?
**A**: When a client sends a multipart file with a malicious filename like `../../../../etc/passwd`, the server extracts only the final component using `Path(raw_filename).name` and strips surrounding whitespace. Furthermore, the file is saved under a randomized UUID prefix in an isolated staging directory (`data/uploads/{uuid}_{basename}`), completely neutralizing any directory traversal or file-overwrite vectors.
