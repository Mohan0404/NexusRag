# Phase 6 — ChromaDB + Vector Storage

## 1. Objective

Phase 6 implements the **persistent vector storage layer** for NexusRAG using **ChromaDB**. This layer sits between the embedding service (Phase 5) and the future retrieval layer (Phase 7).

The `ChromaStore` abstraction accepts pre-embedded document chunks (`EmbeddedChunk` objects from Phase 5) and persists them into a named ChromaDB collection with deterministic IDs, sanitized metadata, and upsert-based idempotent storage semantics.

Phase 6 does **NOT** implement:
- Similarity search / retrieval (Phase 7)
- Query embedding (Phase 7)
- Top-K logic, reranking, BM25, hybrid search (Phase 7)
- Embedding generation (Phase 5)

---

## 2. Files Created / Modified

| File | Action | Purpose |
| :--- | :--- | :--- |
| `backend/app/vectordb/chroma_store.py` | **Implemented** | Core `ChromaStore` abstraction with CRUD operations, deterministic ID generation, metadata sanitization, and domain exceptions |
| `backend/app/vectordb/__init__.py` | **Implemented** | Public API exports for the vectordb module |
| `backend/app/core/config.py` | **Modified** | Added `VectorDBConfig` Pydantic model, `vectordb` field in `Settings`, convenience properties (`vectordb_provider`, `vectordb_collection_name`), and YAML parser branch |
| `backend/config.yaml` | **Modified** | Added `vectordb:` configuration block with `provider` and `collection_name` |
| `backend/requirements.txt` | **Modified** | Added `chromadb>=1.0.0` |
| `backend/tests/test_vectordb.py` | **Created** | 17 integration/unit tests covering full ChromaStore behavior |

---

## 3. Architecture

### Data Flow (Phase 6 Scope)

```text
Phase 3: DocumentService.ingest_file()
    → List[Document]
        ↓
Phase 4: DocumentChunker.chunk_documents()
    → List[Document] (with chunk_index, chunk_count, char_count metadata)
        ↓
Phase 5: GeminiEmbeddingService.embed_documents()
    → List[EmbeddedChunk] (content + 768-dim vector + metadata)
        ↓
Phase 6: ChromaStore.add_embedded_chunks()          ← THIS PHASE
    → Persistent ChromaDB collection on disk
```

### Conceptual Record Structure

```text
┌─────────────────────────────────────────────────────────┐
│                    ChromaDB Record                       │
├─────────────┬───────────────────────────────────────────┤
│ ID          │ sha256("architecture.pdf::chunk_0")[:16]  │
│ Document    │ "NexusRAG provides sub-second retrieval…" │
│ Embedding   │ [0.0123, -0.0456, …, 0.0891] (768 dims) │
│ Metadata    │ {source, file_type, page, chunk_index, …} │
└─────────────┴───────────────────────────────────────────┘
```

### Architectural Separation

```text
Embedding Service (Phase 5)
      ↓
Embedded Chunks (EmbeddedChunk dataclass)
      ↓
ChromaStore (Phase 6)          ← Application abstraction layer
      ↓
ChromaDB PersistentClient      ← Infrastructure
      ↓
./data/chroma/                 ← Persistent on-disk storage
```

The rest of the application never touches ChromaDB directly. All vector store operations go through the `ChromaStore` class.

---

## 4. File-by-File Walkthrough

### `backend/app/vectordb/chroma_store.py`

**Core class: `ChromaStore`**

Responsibilities:
- Manages a single named ChromaDB collection via `chromadb.PersistentClient`.
- Accepts `List[EmbeddedChunk]` from Phase 5 and upserts them with deterministic IDs.
- Sanitizes metadata to ChromaDB-supported primitives (strips `None` values, converts unsupported types to strings).
- Provides read operations (`get_by_ids`, `get_by_source`) and delete operations (`delete_by_ids`, `delete_by_source`).
- Reports collection statistics (`count`, `collection_info`).
- Supports collection reset for re-embedding scenarios (`reset_collection`).

**Constructor parameters:**
```python
ChromaStore(
    settings=None,           # Defaults to get_settings()
    persist_directory=None,  # Defaults to Settings.CHROMA_PATH
    collection_name=None,    # Defaults to Settings.vectordb_collection_name
)
```

**Exception hierarchy:**
```python
VectorStoreError          # Base exception for all vector store failures
├── CollectionError       # Collection creation/access/drop failures
├── PersistenceError      # Invalid/inaccessible storage path
├── InvalidEmbeddingError # Empty vectors, dimension mismatch
└── MetadataError         # Unsupported metadata types
```

**Key methods:**

| Method | Purpose |
| :--- | :--- |
| `get_or_create_collection()` | Opens or creates the named ChromaDB collection |
| `add_embedded_chunks(chunks)` | Upserts EmbeddedChunk objects → returns count |
| `get_by_ids(ids)` | Retrieves records by deterministic IDs |
| `get_by_source(source)` | Retrieves all chunks from a source file |
| `delete_by_ids(ids)` | Removes specific chunks |
| `delete_by_source(source)` | Removes all chunks from a source document |
| `count()` | Returns total stored chunk count |
| `collection_info()` | Returns collection name, count, path, provider |
| `reset_collection()` | Drops and recreates collection (for re-embedding) |
| `generate_chunk_id(source, chunk_index)` | Static: deterministic SHA-256 based ID |

### `backend/app/vectordb/__init__.py`

Clean public API exposing `ChromaStore` and all domain exceptions.

### `backend/app/core/config.py` — `VectorDBConfig`

New Pydantic model added:

```python
class VectorDBConfig(BaseModel):
    provider: str = "chroma"
    collection_name: str = "nexusrag_documents"
```

Registered in `Settings` as `vectordb: VectorDBConfig`, with convenience properties:
- `Settings.vectordb_provider` → `"chroma"`
- `Settings.vectordb_collection_name` → `"nexusrag_documents"`

The persist directory is **not** in `VectorDBConfig` — it remains in `Settings.CHROMA_PATH` (environment-driven via `.env`) because filesystem paths are infrastructure concerns, not algorithm hyperparameters.

### `backend/config.yaml`

```yaml
vectordb:
  provider: chroma
  collection_name: "nexusrag_documents"
```

---

## 5. Chunk ID Strategy

### Algorithm

```python
import hashlib

def generate_chunk_id(source: str, chunk_index: int) -> str:
    raw = f"{source}::chunk_{chunk_index}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
```

### Properties

| Property | Guarantee |
| :--- | :--- |
| **Deterministic** | Same file + same chunk position → identical ID every time |
| **Idempotent** | Re-ingesting `report.pdf` produces the same IDs → `upsert` replaces cleanly |
| **Collision-resistant** | 16 hex chars = 64 bits of entropy |
| **Stable** | Does not depend on embedding values or model version |
| **No random UUIDs** | UUIDs would cause duplication on re-ingestion |

### Examples

```text
"architecture.pdf::chunk_0" → "a3b9c7d1e4f50826"
"architecture.pdf::chunk_1" → "f1e2d3c4b5a69078"
"hr-policy.txt::chunk_0"    → "7890abcdef123456"
```

---

## 6. Persistence Strategy

- **Client**: `chromadb.PersistentClient(path=persist_directory)`
- **Path source**: `Settings.CHROMA_PATH` (defaults to `./data/chroma`, overridable via `.env`)
- **Automatic persistence**: ChromaDB 1.5.9 writes to disk on every mutation — no manual `persist()` call needed.
- **Cross-instance durability**: Verified that data survives across separate `ChromaStore` instances pointing at the same directory.

---

## 7. Metadata Strategy

### Phase 3/4 Metadata Fields (All ChromaDB-Compatible)

| Field | Type | Origin |
| :--- | :--- | :--- |
| `source` | `str` | Phase 3 loaders |
| `file_name` | `str` | Phase 3 loaders |
| `file_path` | `str` | Phase 3 loaders |
| `file_type` | `str` | Phase 3 loaders |
| `page` | `int` | Phase 3 loaders |
| `total_pages` | `int` | Phase 3 loaders |
| `file_size_bytes` | `int` | Phase 3 loaders |
| `chunk_index` | `int` | Phase 4 chunker |
| `chunk_count` | `int` | Phase 4 chunker |
| `char_count` | `int` | Phase 4 chunker |

### Sanitization

ChromaDB 1.5.9 rejects `None` metadata values (`TypeError`). The `_sanitize_metadata()` method:
1. Strips keys with `None` values.
2. Converts unsupported types to their string representations.
3. Logs warnings for unexpected metadata types.

This defensive layer isolates ChromaDB-specific constraints inside the vector store, protecting upstream phases from storage format concerns.

---

## 8. Duplicate / Upsert Behavior

**Strategy: Deterministic upsert via `collection.upsert()`**

- Because IDs are deterministic (`sha256(source::chunk_N)[:16]`), re-ingesting the same document produces identical IDs.
- `upsert` replaces existing records with potentially updated text, embeddings, and metadata.
- No duplicates accumulate.

**Edge case — changed chunking parameters:**
- If `chunk_size` changes, the same document produces different chunks at different indices → different IDs → old IDs become orphaned.
- V1 solution: call `delete_by_source("report.pdf")` before re-ingesting, or use `reset_collection()` for a full rebuild.

---

## 9. Error Handling

| Scenario | Exception | Behavior |
| :--- | :--- | :--- |
| Invalid/inaccessible storage path | `PersistenceError` | Fails before any collection operations |
| Collection creation failure | `CollectionError` | Wraps underlying ChromaDB errors |
| Empty embedding vector | `InvalidEmbeddingError` | Caught before sending to ChromaDB |
| Dimension mismatch during upsert | `InvalidEmbeddingError` | Detected from ChromaDB error message |
| Generic ChromaDB upsert failure | `VectorStoreError` | Wraps raw exceptions with context |
| Collection drop/reset failure | `CollectionError` | Wraps drop and recreation errors |
| `None` values in metadata | Silently stripped | Logged at DEBUG level |

---

## 10. Configuration Summary

### Environment Variables (`.env`)

```env
CHROMA_PATH=./data/chroma
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

Already existed. No changes required.

### YAML Configuration (`config.yaml`)

```yaml
vectordb:
  provider: chroma
  collection_name: "nexusrag_documents"
```

New block added in Phase 6.

### Pydantic Settings (`config.py`)

```python
class VectorDBConfig(BaseModel):
    provider: str = "chroma"
    collection_name: str = "nexusrag_documents"
```

---

## 11. Dependencies

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `chromadb` | `>=1.0.0` (installed: `1.5.9`) | Persistent vector database |

No LangChain-ChromaDB adapter is used. The native `chromadb` Python API is used directly behind the `ChromaStore` abstraction, providing full control over ID generation, upsert semantics, metadata sanitization, and error handling.

---

## 12. Testing

### Test Execution

```powershell
.venv\Scripts\Activate.ps1; cd NexusRag/backend; python -m pytest -v
```

### Complete Test Results (63 Passed, 0 Failed)

```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Academic-Projects\RAG\NexusRag\backend
plugins: anyio-4.15.1, langsmith-0.12.1
collected 63 items

tests/test_chunking.py (11 tests) ............................ [ 17%]
tests/test_config.py (6 tests) ............................... [ 26%]
tests/test_embeddings.py (12 tests) .......................... [ 46%]
tests/test_health.py (3 tests) ............................... [ 50%]
tests/test_ingestion.py (10 tests) ........................... [ 66%]
tests/test_logging.py (4 tests) .............................. [ 73%]
tests/test_vectordb.py (17 tests) ............................ [100%]

======================= 63 passed, 2 warnings in 8.57s ========================
```

### Test Coverage (test_vectordb.py — 17 tests)

| # | Test | Verifies |
| :--- | :--- | :--- |
| 1 | `test_collection_creation` | Named collection created with correct info |
| 2 | `test_persistent_collection_reopening` | Data survives across ChromaStore instances |
| 3 | `test_add_embedded_chunks` | EmbeddedChunks upserted into collection |
| 4 | `test_stored_text_retrieval` | Retrieved documents match original content |
| 5 | `test_stored_metadata_preserved` | All 10 Phase 3/4 metadata fields round-trip |
| 6 | `test_stored_ids_correct` | IDs match `generate_chunk_id()` output |
| 7 | `test_multiple_chunks_stored` | Multi-source batch produces correct count |
| 8 | `test_upsert_idempotency` | Same chunks twice → count unchanged, content updated |
| 9 | `test_delete_by_ids` | Specific IDs removed |
| 10 | `test_delete_by_source` | All chunks from a source removed |
| 11 | `test_collection_count_and_info` | Count and info return correct values |
| 12 | `test_invalid_embedding_handling` | Empty vectors raise InvalidEmbeddingError |
| 13 | `test_empty_input_handling` | Empty list returns 0, no error |
| 14 | `test_metadata_sanitization` | None values stripped before insertion |
| 15 | `test_reset_collection` | Drop + recreate zeros the collection |
| 16 | `test_get_by_source` | Source-filtered retrieval returns correct chunks |
| 17 | `test_generate_chunk_id_deterministic` | Idempotent and collision-resistant IDs |

---

## 13. Design Decisions

1. **Native ChromaDB Client (not LangChain wrapper)**: Using `chromadb.PersistentClient` directly rather than `langchain-chroma` gives full control over ID generation, upsert semantics, metadata sanitization, and error handling without an opaque abstraction layer.

2. **Deterministic SHA-256 IDs**: Instead of random UUIDs, chunk IDs are derived from `source + chunk_index`. This makes re-ingestion idempotent — the same document always produces the same IDs, enabling clean upserts.

3. **Metadata Sanitization Inside ChromaStore**: ChromaDB's `None` rejection is handled as an implementation detail of the storage layer. Upstream phases are not burdened with storage format constraints.

4. **Lazy Client Initialization**: The ChromaDB `PersistentClient` is created on first use (`_ensure_client()`), not at import time. This allows tests and health checks to run without touching the filesystem.

5. **Separation of Configuration Concerns**: The collection name is a non-secret algorithm parameter (in `config.yaml`), while the persist directory is an infrastructure path (in `.env`). This follows the established Phase 2 pattern.

6. **Upsert Over Insert**: Using `collection.upsert()` instead of `collection.add()` provides built-in idempotency without requiring pre-existence checks.

---

## 14. Important Notes for Future Phases

> **Changing the embedding model or dimensionality requires rebuilding the vector store.**
>
> If `embeddings.model` or `embeddings.output_dimension` is changed in `config.yaml`, all existing vectors in ChromaDB become incompatible. Use `ChromaStore.reset_collection()` followed by a full re-embedding pipeline to rebuild.

---

## 15. Connection to Phase 7 (Retrieval)

Phase 7 will add similarity search on top of the ChromaStore:

```text
User Query
    ↓
GeminiEmbeddingService.embed_query(query)  ← Phase 5
    ↓
Query Vector (768-dim)
    ↓
ChromaDB collection.query(query_embeddings=..., n_results=top_k)  ← Phase 7
    ↓
Top-K Ranked Document Chunks
```

The `ChromaStore` class may be extended (or a `Retriever` class created in `app/retrieval/retriever.py`) to expose `similarity_search()` using ChromaDB's `collection.query()` method.

---

## 16. Verification Checklist

- [x] ChromaDB persistent collection created via `PersistentClient`
- [x] EmbeddedChunks from Phase 5 upserted with deterministic IDs
- [x] Chunk text stored and retrievable
- [x] All 10 Phase 3/4 metadata fields preserved through round-trip
- [x] Deterministic IDs prevent duplication on re-ingestion
- [x] Upsert idempotency verified (count stable, content updated)
- [x] Delete by ID and delete by source both functional
- [x] Collection statistics and info accessible
- [x] Collection reset (drop + recreate) functional
- [x] Empty input handled gracefully
- [x] Invalid embeddings raise `InvalidEmbeddingError`
- [x] Metadata sanitization strips `None` values
- [x] Data persists across ChromaStore instances
- [x] Configuration centralized (VectorDBConfig + Settings.CHROMA_PATH)
- [x] No similarity search implemented (Phase 7)
- [x] Complete test suite passes (63/63 tests green across Phases 1–6)
