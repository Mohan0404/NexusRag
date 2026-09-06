# Phase 7 — Similarity Retrieval

## 1. Objective

Phase 7 implements the **similarity retrieval layer** for NexusRAG. Given a user query, it generates a query embedding, searches ChromaDB for the most similar document chunks, and returns structured results with content, metadata, and distance information.

This phase bridges the gap between vector storage (Phase 6) and the future RAG answer generation pipeline (Phase 8/9).

Phase 7 does **NOT** implement:
- LLM generation or prompt construction (Phase 8/9)
- Redis caching (Phase 10)
- FastAPI endpoints (Phase 11)
- Hybrid search, BM25, reranking, or query expansion
- Agents or multi-query retrieval

---

## 2. Files Created/Modified

| File | Action | Responsibility |
| :--- | :--- | :--- |
| `backend/app/retrieval/retriever.py` | **Implemented** | `Retriever` class orchestrating the full query → embedding → search → results pipeline. Contains `RetrievedChunk` dataclass and retrieval exceptions. |
| `backend/app/retrieval/__init__.py` | **Implemented** | Public API exports for the retrieval module. |
| `backend/app/vectordb/chroma_store.py` | **Modified** | Added `similarity_search()` method — keeps ChromaDB query internals inside the abstraction. |
| `backend/tests/test_retrieval.py` | **Created** | 15 tests covering successful retrieval, error handling, configuration, and edge cases. |
| `backend/docs/phases/phase-07-similarity-retrieval.md` | **Created** | This walkthrough document. |

No changes to `config.yaml`, `config.py`, `.env`, or `requirements.txt` — `top_k` already existed in `RAGConfig`.

---

## 3. Retrieval Architecture

```text
User Query
    ↓
Retriever._validate_query()
    ↓ (rejects empty/whitespace queries)
GeminiEmbeddingService.embed_query()       ← Phase 5
    ↓ (RETRIEVAL_QUERY task type, 768-dim vector)
ChromaStore.similarity_search()            ← Phase 6, extended in Phase 7
    ↓ (L2 squared distance search)
ChromaDB collection.query()                ← Infrastructure
    ↓ (raw nested result)
ChromaStore unwraps outer list             ← Phase 7 addition
    ↓ (flat dict: ids, documents, metadatas, distances)
Retriever._build_retrieved_chunks()        ← Phase 7
    ↓
List[RetrievedChunk]                       ← Clean application-level output
```

### Dependency Diagram

```text
┌──────────────┐     ┌───────────────────────┐     ┌──────────────┐
│   Retriever  │────▶│ BaseEmbeddingService  │     │  ChromaStore  │
│  (Phase 7)   │     │     (Phase 5)          │     │  (Phase 6)   │
│              │────▶│                         │     │              │
│              │     └───────────────────────┘     │              │
│              │────────────────────────────────────▶│              │
└──────────────┘                                     └──────────────┘
       │                                                    │
       ▼                                                    ▼
RetrievedChunk                                    chromadb.Collection
  (application)                                     (infrastructure)
```

---

## 4. How Similarity Search Works

### Query Embedding

When a user submits a query like "What is the employee leave policy?", the embedding service converts it into a dense numerical vector of 768 dimensions using Gemini Embedding 2 with the `RETRIEVAL_QUERY` task type.

This task type is **asymmetric** — it is optimized differently from `RETRIEVAL_DOCUMENT` (used when indexing chunks). The asymmetry allows the model to learn that queries are short and intent-focused while documents are longer and content-rich.

### Document Embeddings

During ingestion (Phases 3–5), each document chunk was embedded using `RETRIEVAL_DOCUMENT` task type and stored in ChromaDB alongside its text content and metadata.

### Vector Space

Both query and document embeddings exist in the same 768-dimensional vector space. Semantically similar content maps to nearby regions of this space. The core insight: **similarity in meaning corresponds to proximity in vector space**.

### Vector Distance

ChromaDB's default metric is **L2 squared (Euclidean squared)** distance:

```
d(q, d) = Σ (q_i - d_i)²
```

- **Lower distance = higher similarity**
- `0.0` = identical vectors
- There is no upper bound (unlike cosine similarity which ranges 0–1)

### Nearest-Neighbor Search

ChromaDB performs approximate nearest-neighbor (ANN) search using HNSW (Hierarchical Navigable Small World) graphs internally. For each query vector, it finds the `n_results` closest document vectors by L2 squared distance.

### Top-K Retrieval

The system returns the K nearest document chunks. The default `top_k=4` was chosen as a practical starting point — enough context for an LLM to synthesize an answer, while limiting noise from marginally relevant chunks.

---

## 5. ChromaDB Integration

### ChromaStore Extension

Phase 7 added one new method to `ChromaStore`:

```python
def similarity_search(
    self,
    query_embedding: List[float],
    n_results: int = 4,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
```

This method:
1. Takes a pre-computed query vector (generated by the embedding service).
2. Delegates to `collection.query(query_embeddings=[...], n_results=..., include=[...])`.
3. Unwraps the outer list wrapper that ChromaDB returns for multi-query support.
4. Returns a flat dictionary: `{ids: [...], documents: [...], metadatas: [...], distances: [...]}`.

### Why Similarity Search Lives Inside ChromaStore

ChromaDB's `collection.query()` returns a nested structure (`[[...]]`) designed for batch queries. Unwrapping this and handling the `include` parameter list are ChromaDB-specific implementation details. Keeping them inside `ChromaStore` means:
- The `Retriever` never touches raw ChromaDB types.
- Switching vector databases would only require modifying `ChromaStore`, not `Retriever`.
- The `where` filter parameter is available for future metadata-filtered searches.

### Retriever Does Not Manipulate ChromaDB Internals

The `Retriever` interacts with `ChromaStore` through two operations:
1. `chroma_store.similarity_search(query_embedding, n_results)` — for searching
2. No direct `import chromadb` or collection access in `retriever.py`

---

## 6. Top-K

### What Top-K Means

Top-K retrieval returns the K document chunks with the smallest distance (highest similarity) to the query vector. In a collection of thousands of chunks, only the K most relevant are returned.

### Why K=4

The project starts with `top_k=4` because:
- **Sufficient context**: 4 chunks of ~800 characters each provides ~3,200 characters of context — enough for most question-answering tasks.
- **LLM context efficiency**: Sending too many chunks wastes LLM context window tokens and may introduce noise.
- **Common default**: RAG systems typically start with 3–5 and tune based on evaluation metrics.

### Configuration

Top-K is configurable via `config.yaml`:

```yaml
rag:
  top_k: 4
```

Accessed via `Settings.top_k`. The `Retriever` accepts an optional `top_k` parameter override:

```python
# Use default from config.yaml
results = retriever.retrieve("query")

# Override for a specific query
results = retriever.retrieve("query", top_k=8)
```

---

## 7. Distance vs Similarity

### What ChromaDB Returns

ChromaDB 1.5.9 with default settings returns **L2 squared distances** via the `distances` field in query results.

```python
result["distances"] → [0.020, 0.320, 1.540, 2.010]
```

### This Is NOT a Similarity Score

| Concept | Range | Interpretation |
| :--- | :--- | :--- |
| L2 squared distance | [0, ∞) | Lower = more similar |
| Cosine similarity | [-1, 1] | Higher = more similar |
| Normalized score | [0, 1] | Higher = more similar |

ChromaDB's distance values are unbounded positive numbers. Calling them "similarity scores" would be misleading.

### How the Application Represents It

The `RetrievedChunk` dataclass uses the field name `distance`:

```python
@dataclass
class RetrievedChunk:
    content: str
    metadata: Dict[str, Any]
    distance: float  # L2 squared distance (lower = more similar)
```

The field is documented as ChromaDB L2 squared distance. No artificial normalization is applied because:
1. A normalized "relevance score" would require knowing the maximum possible distance, which depends on the embedding model and data distribution.
2. Converting `1 / (1 + distance)` is sometimes used but would be a project-specific design choice better deferred to Phase 14 (RAG evaluation).

---

## 8. Metadata Preservation

Retrieved chunks preserve the full metadata pipeline:

| Field | Origin | Purpose |
| :--- | :--- | :--- |
| `source` | Phase 3 (ingestion) | Source filename for citations |
| `file_name` | Phase 3 | Display name |
| `file_path` | Phase 3 | Full filesystem path |
| `file_type` | Phase 3 | pdf, txt, md |
| `page` | Phase 3 | Page number for citations |
| `total_pages` | Phase 3 | Document length context |
| `file_size_bytes` | Phase 3 | Size information |
| `chunk_index` | Phase 4 (chunking) | Position within document |
| `chunk_count` | Phase 4 | Total chunks from document |
| `char_count` | Phase 4 | Chunk character length |

This metadata will be consumed by future phases:
- **Phase 9 (RAG pipeline)**: Include source citations in LLM prompts.
- **Phase 11 (API endpoints)**: Return source information to the frontend.
- **Phase 12 (React frontend)**: Display "Source: hr-policy.pdf, page 3" to users.

---

## 9. Error Handling

### Exception Hierarchy

```text
RetrievalError                      # Base retrieval exception
├── EmptyQueryError                 # Empty/whitespace query (ValueError)
├── QueryEmbeddingError             # Embedding service failure
└── VectorSearchError               # ChromaDB query failure
```

### Error Translation

| Scenario | Source Exception | Retrieval Exception |
| :--- | :--- | :--- |
| Empty/whitespace query | (validated locally) | `EmptyQueryError` |
| Embedding service API failure | `EmbeddingProviderError` | `QueryEmbeddingError` |
| Embedding rate limit | `EmbeddingProviderError` | `QueryEmbeddingError` |
| Missing API key | `MissingAPIKeyError` | `QueryEmbeddingError` |
| ChromaDB query failure | `VectorStoreError` | `VectorSearchError` |
| Empty collection | (no error) | Returns `[]` |
| Fewer results than top_k | (no error) | Returns available results |

### Design Decision: Wrapping vs Propagating

The `Retriever` wraps lower-level exceptions into its own hierarchy because:
1. **Caller isolation**: Future phases (API endpoints, RAG pipeline) should not need to import embedding or vector store exceptions.
2. **Context enrichment**: Wrapped exceptions include retrieval-specific context ("Failed to generate embedding for query").
3. **Original exception preserved**: The `__cause__` chain is maintained via `raise ... from e`.

---

## 10. Testing

### Test Execution

```powershell
python -m pytest tests/test_retrieval.py -v
```

### Test Architecture

- **`FakeEmbeddingService`**: A deterministic implementation of `BaseEmbeddingService` that returns predictable vectors without calling the Gemini API.
- **Real `ChromaStore`**: Tests use `chromadb.PersistentClient` with `tmp_path` fixture — real ChromaDB operations with temporary storage (matching Phase 6 test architecture).
- **No external dependencies**: No Gemini API calls, no persistent ChromaDB installation.

### Complete Test Results (78 Passed, 0 Failed)

```text
tests/test_chunking.py     — 11 passed
tests/test_config.py       —  6 passed
tests/test_embeddings.py   — 12 passed
tests/test_health.py       —  3 passed
tests/test_ingestion.py    — 10 passed
tests/test_logging.py      —  4 passed
tests/test_retrieval.py    — 15 passed
tests/test_vectordb.py     — 17 passed
======================== 78 passed in 8.21s =======================
```

### Retrieval Test Coverage (15 tests)

| # | Test | Verifies |
| :--- | :--- | :--- |
| 1 | `test_successful_retrieval` | Valid query returns `RetrievedChunk` objects |
| 2 | `test_query_embedding_generated` | `embed_query()` called with correct query string |
| 3 | `test_chromadb_queried_with_embedding` | ChromaStore receives the generated vector |
| 4 | `test_top_k_respected` | 5 chunks stored, top_k=3 → 3 returned |
| 5 | `test_result_ordering_preserved` | Results in ascending distance order |
| 6 | `test_result_content_preserved` | Content matches stored text |
| 7 | `test_result_metadata_preserved` | source, page, chunk_index, file_type round-trip |
| 8 | `test_distance_preserved` | Non-negative float distances preserved |
| 9 | `test_empty_query_rejected` | `""` → `EmptyQueryError` |
| 10 | `test_whitespace_query_rejected` | `"   \n\t  "` → `EmptyQueryError` |
| 11 | `test_empty_collection_returns_empty` | Empty collection → `[]`, no error |
| 12 | `test_fewer_results_than_top_k` | 5 chunks, top_k=20 → 5 returned |
| 13 | `test_embedding_failure_propagated` | `EmbeddingProviderError` → `QueryEmbeddingError` |
| 14 | `test_chromadb_failure_handled` | `VectorStoreError` → `VectorSearchError` |
| 15 | `test_configuration_respected` | Default top_k=4 from Settings used |

---

## 11. Design Decisions

### Why Dense Vector Search

Dense vector search using Gemini Embedding 2 was selected because:
- It captures **semantic similarity** (meaning), not just keyword overlap.
- "What is the PTO policy?" matches "Employees receive 20 days of paid time off" even without shared keywords.
- The embedding model is already integrated (Phase 5).
- Dense search is the standard first step in production RAG systems.

### Why NOT Hybrid Search

Hybrid search (combining dense vectors with BM25/sparse retrieval) was not added because:
- Phase 7 is intentionally simple — dense-only V1.
- BM25 requires a separate index and scoring mechanism.
- Hybrid search adds complexity (score normalization, weight tuning) that is better addressed in Phase 14 (evaluation) after measuring dense-only performance.

### Why NOT Reranking

Cross-encoder reranking was not added because:
- It requires an additional model (e.g. cross-encoder/ms-marco) and inference cost.
- Reranking is a refinement step that should be evaluated after the baseline retrieval quality is measured.
- The current top_k=4 is small enough that reranking provides minimal benefit.

### Why Retrieval Is Separated From ChromaStore

The `Retriever` orchestrates the pipeline; `ChromaStore` handles storage operations. This separation:
- **Single Responsibility**: ChromaStore manages persistence; Retriever manages the query workflow.
- **Testability**: The Retriever can be tested with a mock ChromaStore (and vice versa).
- **Swappability**: ChromaStore could be replaced with Pinecone, Weaviate, or Qdrant without changing the Retriever's logic.

### Why Retrieval Does Not Call the LLM

Retrieval and generation are distinct concerns:
- **Retrieval** finds relevant context.
- **Generation** synthesizes an answer from that context.

Separating them enables:
- Independent evaluation of retrieval quality (Phase 14).
- Swapping LLM providers without touching retrieval.
- Caching retrieval results independently (Phase 10).

---

## 12. Future Improvements

The following improvements are possible but NOT implemented in Phase 7:

### Similarity Threshold
Filter out low-relevance chunks by discarding results above a distance threshold. Requires evaluation data to calibrate the threshold.

### Hybrid Vector + BM25
Combine dense vector search with sparse keyword-based BM25 retrieval. Useful when exact keyword matches matter (e.g. technical terms, product names).

### Reranking
Use a cross-encoder model to re-score the top-K results after initial retrieval. Improves precision at the cost of additional inference latency.

### Query Expansion
Reformulate or expand the user query using an LLM before embedding. Can improve recall for ambiguous or short queries.

### Multi-Query Retrieval
Generate multiple query variants and merge their results. Captures different aspects of the user's intent.

---

## 13. Future Phase Connection

### Phase 8 (LLM Integration)
Will integrate Gemini LLM via OpenRouter. The LLM will consume `RetrievedChunk` objects to generate answers.

### Phase 9 (RAG Pipeline)
Will orchestrate the full Retrieval-Augmented Generation flow:

```text
User Query
    ↓
Retriever.retrieve()       ← Phase 7
    ↓
List[RetrievedChunk]
    ↓
Prompt Construction        ← Phase 9
    ↓
LLM Generation             ← Phase 8
    ↓
Answer with Citations
```

The `RetrievedChunk.content` will be injected into the LLM prompt as context. The `RetrievedChunk.metadata` (source, page) will be used to generate source citations in the answer.

---

## 14. Interview Knowledge

### Embeddings
Embeddings are dense numerical vector representations of text. They map semantic meaning into a high-dimensional space where similar concepts have nearby vectors. Gemini Embedding 2 produces 768-dimensional vectors using Matryoshka Representation Learning.

### Vector Similarity
Two texts are semantically similar if their embedding vectors are close in vector space. "Similarity" is measured by distance metrics — common choices are L2 (Euclidean), cosine, and inner product.

### Nearest-Neighbor Search
Given a query vector, find the K vectors in the database closest to it by some distance metric. Exact NN search is O(n) and impractical for large datasets, so vector databases use approximate methods like HNSW (Hierarchical Navigable Small World graphs).

### Top-K
The K parameter controls how many results are returned. Too small K may miss relevant context; too large K adds noise and wastes LLM tokens. K=4 is a common starting point for RAG systems.

### Vector Databases
Specialized databases (ChromaDB, Pinecone, Weaviate, Qdrant, Milvus) optimized for storing high-dimensional vectors and performing approximate nearest-neighbor search at scale. They provide persistence, indexing (HNSW, IVF), and metadata filtering.

### Retrieval vs Generation
**Retrieval** finds relevant documents from a corpus. **Generation** produces natural language answers. RAG separates these concerns: retrieval provides grounding context, generation synthesizes it into a coherent answer. This separation allows independent optimization and evaluation.

### Distance vs Similarity
- **Distance** (L2, Euclidean): lower = more similar. Range: [0, ∞).
- **Similarity** (cosine): higher = more similar. Range: [-1, 1] (or [0, 1] for normalized vectors).
- ChromaDB defaults to L2 squared distance. The application preserves this raw value rather than applying an arbitrary normalization.

### Why Metadata Matters
Metadata enables **source attribution** — telling users where an answer came from. In a RAG system, citations build trust. Metadata also enables **filtered retrieval** (search only within a specific document), **deduplication** (avoid returning multiple chunks from the same page), and **evaluation** (measure if the correct source was retrieved).

### Dense vs Sparse Retrieval
- **Dense retrieval** (embedding-based): captures semantic meaning, handles paraphrases, works across languages. Requires an embedding model.
- **Sparse retrieval** (BM25, TF-IDF): matches exact keywords, no model needed, fast. Fails on paraphrases.
- **Hybrid**: combines both. Best of both worlds but adds complexity.

### Why Retrieval Should Be Separated From Vector Storage
The `Retriever` orchestrates the pipeline (query validation → embedding → search → result conversion). The `ChromaStore` manages storage operations (persistence, indexing, CRUD). Separating them:
- Enables swapping vector databases without changing retrieval logic.
- Allows independent testing of each layer.
- Follows the Single Responsibility Principle.
- Mirrors how production systems work (e.g., LangChain's `VectorStore` vs `Retriever` separation).

---

## 15. Verification Checklist

- [x] Retriever accepts user query and returns `List[RetrievedChunk]`
- [x] Query embedding generated via `embed_query()` with `RETRIEVAL_QUERY` task type
- [x] ChromaDB similarity search via `ChromaStore.similarity_search()`
- [x] Top-K=4 configurable from `config.yaml` (rag.top_k)
- [x] Top-K overridable per query via `retrieve(query, top_k=N)`
- [x] Results ordered by ascending distance (most similar first)
- [x] Content, metadata, and distance preserved in RetrievedChunk
- [x] Distance represented accurately as L2 squared (not fake similarity score)
- [x] Empty/whitespace queries raise EmptyQueryError
- [x] Embedding failures wrapped as QueryEmbeddingError
- [x] ChromaDB failures wrapped as VectorSearchError
- [x] Empty collection returns empty list (no error)
- [x] Fewer results than top_k returns available results (no error)
- [x] No LLM generation added
- [x] No Redis caching added
- [x] No hybrid search or reranking added
- [x] No real Gemini API calls in tests
- [x] Complete test suite passes (78/78 across Phases 1–7)
