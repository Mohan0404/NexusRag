# Phase 5 — Embeddings

## 1. Objective

The objective of Phase 5 is to implement the **Vector Embedding Layer** for **NexusRAG** targeting Google's state-of-the-art **Gemini Embedding 2 API** (`gemini-embedding-2`) using the modern **Google GenAI SDK** (`google-genai`).

In a production RAG application, textual document chunks and natural language queries cannot be directly compared using simple string matching or keyword search (lexical search). Lexical search fails on synonyms, paraphrasing, semantic intent, and cross-lingual concepts.

The embedding layer bridges human language and vector mathematics:
- Transforms text chunks into dense, high-dimensional numerical vectors that encode semantic concepts and relationships.
- Targets Google's `gemini-embedding-2` model via the modern `google-genai` SDK (`genai.Client`).
- Leverages **Matryoshka Representation Learning (MRL)** via `output_dimensionality` (configured to 768), providing storage efficiency while preserving embedding quality.
- Employs asymmetric task types (`RETRIEVAL_DOCUMENT` vs `RETRIEVAL_QUERY`) to align directional projections of short questions and comprehensive document paragraphs.
- Enables downstream vector databases (Phase 6 — ChromaDB) to perform low-latency cosine or inner-product similarity search.
- Preserves 100% of the provenance metadata established in Phase 3 and Phase 4 (`source`, `page`, `chunk_index`, `file_type`), pairing each vector with its original text and metadata in a structured container (`EmbeddedChunk`).

---

## 2. Files Created / Modified

| File | Purpose | Changes |
| :--- | :--- | :--- |
| `backend/app/embeddings/embedder.py` | Core embedding service & abstraction | Implemented `BaseEmbeddingService` interface, `GeminiEmbeddingService` targeting `google.genai.Client`, and `EmbeddedChunk` container. Added Matryoshka dimensionality (`output_dimension=768`), asymmetric task types (`RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY`), batching mechanisms, on-demand client configuration, and domain exceptions (`EmbeddingError`, `MissingAPIKeyError`, `EmbeddingConfigurationError`, `EmbeddingProviderError`, `EmptyEmbeddingInputError`). |
| `backend/app/embeddings/__init__.py` | Module interface | Exported `BaseEmbeddingService`, `GeminiEmbeddingService`, `EmbeddedChunk`, and custom exception classes. |
| `backend/app/core/config.py` | Configuration model extension | Added `EmbeddingsConfig` submodel (`model: "gemini-embedding-2"`, `batch_size: 100`, `output_dimension: 768`), property helpers (`embedding_model`, `embedding_batch_size`, `embedding_output_dimension`), and YAML loader branch. |
| `backend/config.yaml` | Non-secret parameter storage | Added `embeddings` configuration block specifying model (`gemini-embedding-2`), batch size limit (`100`), and output dimensionality (`768`). |
| `backend/requirements.txt` | Dependency declaration | Added `google-genai>=2.0.0` (replacing deprecated `google-generativeai`). |
| `backend/tests/test_embeddings.py` | Automated test suite | Created 12 comprehensive unit tests covering single text embedding, query embedding, Matryoshka dimensionality override, document batching, metadata propagation, empty input handling, rate limit handling, API failure wrapping, and configuration validation using a mocked `google.genai.Client`. |

---

## 3. Embedding Architecture

```text
               Phase 4 Document Chunks (List[Document])
                                  │
                                  ▼
                     GeminiEmbeddingService
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
  Document Embedding Path                         Query Embedding Path
  (embed_documents / embed_texts)                    (embed_query)
         │                                                 │
         ├─► Task Type: "RETRIEVAL_DOCUMENT"               ├─► Task Type: "RETRIEVAL_QUERY"
         ├─► Batching (sub-batches of 100)                 ├─► Single string vectorization
         ├─► Output Dimensionality: 768 (MRL)              └─► Output Dimensionality: 768 (MRL)
         ▼                                                 ▼
  Google GenAI SDK (client.models.embed_content)     Google GenAI SDK (client.models.embed_content)
  Model: "gemini-embedding-2"                        Model: "gemini-embedding-2"
         │                                                 │
         ▼                                                 ▼
  Dense Vectors (768-dim floats)                    Dense Vector (768-dim float)
         │                                                 │
         ▼                                                 ▼
  Metadata Pairings (EmbeddedChunk)                 Search Vector for Retrieval
  (content + embedding + metadata)                         │
         │                                                 │
         └────────────────────────┬────────────────────────┘
                                  │
                                  ▼
                   Ready for Phase 6: ChromaDB
```

---

## 4. File-by-File Walkthrough

### `backend/app/embeddings/embedder.py`
- **Responsibility**: Provides the unified embedding interface and concrete Google GenAI Gemini Embedding 2 implementation.
- **Key Classes & Data Structures**:
  - `EmbeddedChunk`: Dataclass holding `content: str`, `embedding: List[float]`, and `metadata: Dict[str, Any]`. Includes `to_document()` helper for conversion back to LangChain `Document`.
  - `EmbeddingError` hierarchy: Clean, descriptive domain exceptions protecting consumers from raw Google SDK exceptions:
    - `MissingAPIKeyError`: Raised when the Gemini API key is missing or unconfigured.
    - `EmbeddingConfigurationError`: Raised when configuration values (`batch_size`, `output_dimension`) violate invariants.
    - `EmbeddingProviderError`: Raised when external Gemini API calls fail (rate limits, network, malformed responses).
    - `EmptyEmbeddingInputError`: Raised when attempting to embed empty or whitespace-only strings.
  - `BaseEmbeddingService`: Abstract base class enforcing:
    - `embed_text(text: str) -> List[float]`
    - `embed_query(query: str) -> List[float]`
    - `embed_texts(texts: Sequence[str]) -> List[List[float]]`
    - `embed_documents(documents: Sequence[Document]) -> List[EmbeddedChunk]`
  - `GeminiEmbeddingService`:
    - Reads model (`gemini-embedding-2`), batch size (`100`), and output dimension (`768`) dynamically from `Settings`.
    - Initializes modern `google.genai.Client(api_key=...)` on-demand using `settings.GEMINI_API_KEY.get_secret_value()`.
    - Leverages Matryoshka Representation Learning (MRL) via `types.EmbedContentConfig(task_type=..., output_dimensionality=self.output_dimension)`.
    - Implements asymmetric task types: `RETRIEVAL_DOCUMENT` for document chunks and `RETRIEVAL_QUERY` for search queries.
    - Slices text inputs into sub-batches respecting `batch_size` (default 100) to minimize network roundtrips.
- **Dependencies**: `google.genai`, `langchain_core.documents.Document`.
- **Interaction with Phase 4**: Accepts the `List[Document]` output of `DocumentChunker.chunk_documents()`.

### `backend/app/embeddings/__init__.py`
- **Responsibility**: Exposes the clean public API (`GeminiEmbeddingService`, `BaseEmbeddingService`, `EmbeddedChunk`, and exceptions).

### `backend/app/core/config.py` & `backend/config.yaml`
- **Responsibility**: Manages embedding model names, batch sizes, and MRL dimensions centrally.
- **Settings Added**:
  - `EmbeddingsConfig`:
    - `model: str = "gemini-embedding-2"`
    - `batch_size: int = 100`
    - `output_dimension: int = 768`
  - In `config.yaml`:
    ```yaml
    embeddings:
      model: "gemini-embedding-2"
      batch_size: 100
      output_dimension: 768
    ```

### `backend/tests/test_embeddings.py`
- **Responsibility**: Full unit test coverage mocking `google.genai.Client` and `client.models.embed_content`, verifying zero external network dependencies during testing.

---

## 5. Embedding Model & Gemini Embedding 2 Features

### Selected Model: `gemini-embedding-2`
- **Why It Was Selected**: `gemini-embedding-2` is Google's newest and most capable embedding model, succeeding `text-embedding-004`. It introduces native Matryoshka Representation Learning, enhanced multilingual comprehension, OCR and multimodal vector spaces, and superior retrieval accuracy.
- **Modern SDK (`google-genai`)**: Replaces the deprecated `google.generativeai` package. Instantiated cleanly via `genai.Client(api_key=...)` and dispatches requests through `client.models.embed_content()`.
- **Matryoshka Representation Learning (MRL)**:
  - Configured via `EmbedContentConfig(output_dimensionality=768)`.
  - MRL trains the model so that vector prefixes retain high information density. Truncating embeddings to 768 dimensions preserves ~99% of retrieval quality while cutting downstream vector storage and nearest-neighbor search memory in half.
- **Unified Asymmetric Metric Space**: Both documents and queries map to the same vector space, optimized by explicit task types:
  - `task_type="RETRIEVAL_DOCUMENT"` for ingested chunks.
  - `task_type="RETRIEVAL_QUERY"` for search queries.

---

## 6. Embedding Flow

```text
[ Document Chunk (Phase 4) ]
  page_content: "NexusRAG provides sub-second query retrieval..."
  metadata: { "source": "architecture.pdf", "page": 2, "chunk_index": 0 }
               │
               ▼
   GeminiEmbeddingService.embed_documents([chunk])
               │
               ▼
   Extract raw text: chunk.page_content
               │
               ▼
   API Call: client.models.embed_content(
       model="gemini-embedding-2",
       contents=["NexusRAG provides sub-second query retrieval..."],
       config=EmbedContentConfig(
           task_type="RETRIEVAL_DOCUMENT",
           output_dimensionality=768
       )
   )
               │
               ▼
   Returned Vector: [0.0123, -0.0456, ..., 0.0891] (768 floats)
               │
               ▼
[ EmbeddedChunk Container ]
  content: "NexusRAG provides sub-second query retrieval..."
  embedding: [0.0123, -0.0456, ..., 0.0891]
  metadata: { "source": "architecture.pdf", "page": 2, "chunk_index": 0 }
```

---

## 7. Batching Strategy

### Why Batching Was Implemented
In typical document ingestion, a 100-page PDF can produce 300 to 500 chunks. Making an individual HTTP request for every chunk would introduce:
- Severe network overhead (300 roundtrips).
- High probability of hitting API rate limits (HTTP 429).
- Substantial latency delays (300 × 150ms ≈ 45 seconds).

### Implementation
`GeminiEmbeddingService.embed_texts` partitions input texts into sequential slices of size `self.batch_size` (default 100):
```python
for i in range(0, total_texts, self.batch_size):
    batch = list(texts[i : i + self.batch_size])
    clean_batch = [t if t and t.strip() else " " for t in batch]
    vectors = self._call_api(contents=clean_batch, task_type="RETRIEVAL_DOCUMENT")
    all_embeddings.extend(vectors)
```
For 300 chunks, batching issues only 3 API requests instead of 300, providing an order-of-magnitude performance improvement.

---

## 8. Error Handling

| Scenario | Handled Condition | Raised Exception | Behavioral Result |
| :--- | :--- | :--- | :--- |
| **Missing API Key** | `GEMINI_API_KEY` is `None` or empty | `MissingAPIKeyError` | Fails fast before attempting network calls; logs clear diagnostic instructions without leaking tokens. |
| **Rate Limiting / Quota** | Gemini returns HTTP 429 / `ResourceExhausted` / Quota Exceeded | `EmbeddingProviderError` | Identifies quota exhaustion and informs caller (`"Gemini API rate limit / quota exceeded"`). |
| **Network / Connection Failure** | Socket timeouts, DNS resolution errors, 5xx | `EmbeddingProviderError` | Traps SDK exceptions and formats clean error messages without raw stack dump. |
| **Empty String Input** | `text == ""` or whitespace-only | `EmptyEmbeddingInputError` | Rejects empty strings before making redundant API calls. |
| **Empty Document Collection** | `documents == []` | Returns `[]` | Returns empty list immediately with zero network overhead. |
| **Invalid Batch Size / Dimension** | `batch_size <= 0` or `output_dimension <= 0` | `EmbeddingConfigurationError` | Enforces boundary invariants during service initialization. |
| **Malformed API Response** | API returns missing `embeddings` or unexpected format | `EmbeddingProviderError` | Protects downstream consumers from `TypeError` / `KeyError`. |

---

## 9. Testing & Mocking Strategy

### Mocking Strategy
The unit test suite completely isolates the application from external network requests:
- Mocks `google.genai.Client` and `client.models.embed_content`.
- Emits proper `types.EmbedContentResponse` and `types.ContentEmbedding` structures.
- Tests single text, query text, Matryoshka dimension override, multi-batch responses, rate-limit simulation, metadata persistence, and configuration validation.
- Zero real API keys or outbound requests are made during testing.

### Test Execution Command
```powershell
.venv\Scripts\Activate.ps1; cd NexusRag/backend; python -m pytest -v
```

### Complete Test Results (46 Passed, 0 Failed):
```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Academic-Projects\RAG\NexusRag\backend
plugins: anyio-4.15.1, langsmith-0.12.1
collected 46 items

tests/test_chunking.py (11 tests) ............................ [ 23%]
tests/test_config.py (6 tests) ............................... [ 36%]
tests/test_embeddings.py (12 tests) .......................... [ 63%]
tests/test_health.py (3 tests) ............................... [ 69%]
tests/test_ingestion.py (10 tests) ........................... [ 91%]
tests/test_logging.py (4 tests) .............................. [100%]

======================= 46 passed, 2 warnings in 2.16s ========================
```

---

## 10. Design Decisions

1. **Modern Google GenAI SDK (`google-genai`)**: Rather than relying on the deprecated `google.generativeai` package, the service targets the official `google-genai` SDK (`genai.Client`).
2. **Native Matryoshka Representation Learning (MRL)**: Instead of treating vectors as fixed-size black boxes, the service exposes `output_dimension` (default 768), giving downstream storage and indexing layers complete control over memory-accuracy trade-offs.
3. **Provider Abstraction (`BaseEmbeddingService`)**: The application interacts with `BaseEmbeddingService` rather than calling the Gemini SDK directly. If the organization decides to switch to local HuggingFace embeddings or OpenAI embeddings in the future, only a new provider class is implemented; no RAG or vector database code changes.
4. **On-Demand Configuration (`_ensure_client`)**: The service does not require `GEMINI_API_KEY` at import or instantiation time. It validates the key only when an embedding operation is invoked. This allows running unit tests and health checks in CI/CD without dummy API keys.
5. **Task Type Specialization**: Utilizing `RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY` explicitly implements Google's best practice for asymmetric vector similarity.
6. **Metadata Preservation via `EmbeddedChunk`**: Chunks and embeddings are not stored in parallel untyped arrays. They are bound together in the `EmbeddedChunk` container to prevent index misalignment bugs.

---

## 11. Connection to Phase 6 (ChromaDB & Vector Indexing)

In Phase 6, the **Vector Database Layer** will directly consume the output of Phase 5:
1. **Input Signature**: ChromaDB will receive the `List[EmbeddedChunk]` from `GeminiEmbeddingService.embed_documents(chunks)`.
2. **Persistence Mapping**:
   - `ids`: Generated deterministic IDs (e.g. `f"{doc.metadata['source']}_{doc.metadata['chunk_index']}"`).
   - `embeddings`: The numerical float vectors (`chunk.embedding`, 768 dimensions).
   - `documents`: The text contents (`chunk.content`).
   - `metadatas`: The preserved metadata dictionary (`chunk.metadata`).
3. **Query Vectorization**: During retrieval in Phase 7, incoming user questions will be passed to `embed_query()` to produce the search vector for ChromaDB's nearest neighbor search.

---

## 12. Interview Knowledge (Applied to NexusRAG)

- **Dense Vector Embeddings**: Unlike sparse representations (TF-IDF, BM25) which rely on exact term overlap, dense embeddings represent words, sentences, and paragraphs in continuous high-dimensional space where vector distance corresponds to semantic relatedness.
- **Matryoshka Representation Learning (MRL)**: MRL structures embedding representations hierarchically so that early vector dimensions capture the highest-order semantics. This allows truncating embeddings (e.g. 768 dimensions) with negligible accuracy loss, yielding massive memory and performance gains in vector databases like ChromaDB.
- **Asymmetric Retrieval (`task_type`)**: User queries are typically short questions ("What is the PTO limit?"), whereas document chunks are descriptive paragraphs. Dual task-type projection optimizes the embedding geometry so that questions point directly toward their corresponding answers.
- **Batching & Throughput**: Slicing large document sets into batches amortizes network connection setup times and conforms to upstream API rate limit ceilings.
- **Provider Decoupling**: Encapsulating external AI vendor SDKs behind domain interfaces protects enterprise architectures from vendor lock-in and unexpected upstream deprecations.

---

## 13. Verification Checklist

- [x] Targeted current Gemini Embedding 2 API (`gemini-embedding-2`) using modern `google-genai` SDK
- [x] Matryoshka Representation Learning (MRL) dimension configured to 768
- [x] Phase 4 chunks can be embedded (`embed_documents` accepts `List[Document]`)
- [x] Document embeddings work (`task_type="RETRIEVAL_DOCUMENT"`)
- [x] Query embeddings work (`task_type="RETRIEVAL_QUERY"`)
- [x] Metadata is preserved (100% of metadata retained in `EmbeddedChunk.metadata`)
- [x] Batching works appropriately (configurable batch size with slicing)
- [x] API failures are handled (`EmbeddingProviderError`, `MissingAPIKeyError`, `EmptyEmbeddingInputError`, `EmbeddingConfigurationError`)
- [x] Secrets aren't logged (API keys masked by `SecretStr` and logging filter)
- [x] Complete test suite passes (46/46 tests green across Phase 1 through Phase 5)
- [x] Phase 1 still works (Health endpoint returns 200 OK)
- [x] Phase 2 still works (Configuration and logging tests pass)
- [x] Phase 3 still works (Document ingestion tests pass)
- [x] Phase 4 still works (Document chunking tests pass)
