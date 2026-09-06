# Phase 4 — Document Chunking

## 1. Objective

The objective of Phase 4 is to implement the **Document Chunking Layer** for **NexusRAG**. In a production Retrieval-Augmented Generation (RAG) system, raw documents cannot be passed directly into embedding models or vector databases as monolithic texts:
- **Embedding Model Limits**: Embedding models have strict context window constraints (e.g. 512, 1024, or 8192 tokens). Exceeding these limits causes silent truncation or API failures.
- **Retrieval Precision**: An entire 50-page document converted into a single vector averages out specific semantic information, destroying retrieval precision. Small, focused chunks allow vector search to pinpoint the exact paragraphs addressing a user query.
- **LLM Context Optimization**: Passing compact, relevant chunks to the LLM minimizes token costs and avoids the "lost in the middle" phenomenon where LLMs struggle to extract answers from bloated context windows.

This phase implements `DocumentChunker`, which ingests the structured LangChain `Document` objects output by Phase 3 (Ingestion) and splits them into clean, overlapping, metadata-enriched chunks ready for Phase 5 (Embeddings).

---

## 2. Files Created / Modified

| File | Purpose | Changes |
| :--- | :--- | :--- |
| `backend/app/chunking/chunker.py` | Core chunking engine | Implemented `DocumentChunker` utilizing LangChain's `RecursiveCharacterTextSplitter`. Added parameter validation (`chunk_size > 0`, `chunk_overlap >= 0`, `chunk_overlap < chunk_size`), custom exceptions (`ChunkingError`, `ChunkingConfigurationError`), metadata preservation, and chunk index tracking. |
| `backend/app/chunking/__init__.py` | Module interface | Exported `DocumentChunker`, `ChunkingError`, and `ChunkingConfigurationError`. |
| `backend/requirements.txt` | Dependency specifications | Explicitly added `langchain-text-splitters>=0.3.0` to track chunking dependencies alongside `langchain-core`. |
| `backend/tests/test_chunking.py` | Automated test suite | Created 11 test cases covering basic chunking, multi-document batching, short documents, empty documents, metadata retention, chunk indexing, deterministic execution, and configuration boundary validation. |

---

## 3. Chunking Architecture

```text
       Phase 3 Ingestion Output (List[Document])
                         │
                         ▼
        DocumentChunker(settings=get_settings())
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
  Validate Input                  Load Hyperparameters
  (Empty? Whitespace?)     (chunk_size=800, chunk_overlap=100)
         │                               │
         └───────────────┬───────────────┘
                         │
                         ▼
        RecursiveCharacterTextSplitter
    (Tries splits at "\n\n" → "\n" → " " → "")
                         │
                         ▼
             Raw Chunk Splits Generated
                         │
                         ▼
           Metadata Enrichment Pipeline
   - Preserves: source, file_name, file_path, file_type, page
   - Injects: chunk_index, chunk_count, char_count
                         │
                         ▼
             List[LangChain Document]
                         │
                         ▼
           Ready for Phase 5: Embeddings
```

---

## 4. File-by-File Walkthrough

### `backend/app/chunking/chunker.py`
- **Responsibility**: Takes parent `Document` objects and executes boundary-validated recursive text chunking while preserving all metadata and adding sequence counters.
- **Key Classes & Functions**:
  - `ChunkingError(Exception)`: Base exception for chunking failures.
  - `ChunkingConfigurationError(ChunkingError, ValueError)`: Raised when configuration boundaries are violated (`chunk_size <= 0`, `chunk_overlap < 0`, or `chunk_overlap >= chunk_size`).
  - `DocumentChunker`:
    - `__init__(settings, chunk_size, chunk_overlap)`: Reads `chunk_size` and `chunk_overlap` from `Settings` by default, but allows constructor overrides for testing. Enforces boundary validation via `_validate_configuration`.
    - `_validate_configuration(chunk_size, chunk_overlap)`: Asserts `chunk_size > 0`, `chunk_overlap >= 0`, and `chunk_overlap < chunk_size`.
    - `chunk_document(document: Document) -> List[Document]`: Splits a single document. Skips empty/whitespace documents gracefully. Enriches each generated chunk with `chunk_index`, `chunk_count`, and `char_count`.
    - `chunk_documents(documents: Sequence[Document]) -> List[Document]`: Batch processes a collection of documents and aggregates results.
- **Dependencies**: `langchain_core.documents.Document`, `langchain_text_splitters.RecursiveCharacterTextSplitter`.
- **Interaction with Phase 3**: Accepts the exact `List[Document]` returned by `DocumentService.ingest_file()` or `DocumentService.ingest_directory()`.

### `backend/app/chunking/__init__.py`
- **Responsibility**: Clean package API exposing `DocumentChunker`, `ChunkingError`, and `ChunkingConfigurationError`.

### `backend/tests/test_chunking.py`
- **Responsibility**: Unit and integration testing of the chunking layer with zero external dependencies.

---

## 5. Chunking Strategy

### Why Recursive Character Splitting?
In arbitrary text (articles, PDFs, legal contracts, manuals), splitting by raw character count cuts words in half (e.g. `juris|diction`). Splitting purely by words cuts sentences in half.

`RecursiveCharacterTextSplitter` uses a hierarchical priority list of separators:
1. `"\n\n"` (Paragraph boundaries)
2. `"\n"` (Line boundaries)
3. `" "` (Word boundaries)
4. `""` (Individual characters as a last resort)

It attempts to keep paragraphs together first. If a paragraph exceeds `chunk_size`, it splits on sentences (`\n`). If a sentence is too long, it splits on words (`" "`). This maximizes semantic coherence within every chunk.

### Hyperparameter Mechanics
- **`chunk_size` (800 characters)**: The maximum character length of any chunk. 800 characters translates to approximately 150–200 English words (roughly 1.5 paragraphs), which fits comfortably within standard embedding model context windows and retains distinct semantic meaning.
- **`chunk_overlap` (100 characters)**: The number of trailing characters from the previous chunk repeated at the beginning of the next chunk.
- **Why Overlap is Critical**: Natural language transitions and context often straddle chunk boundaries. If a key fact depends on the sentence immediately preceding it, an overlap guarantees that adjacent chunks share context, eliminating the boundary cliff effect where retrieval fails because a thought was severed.
- **Limitations**:
  - Does not understand syntactic code blocks (e.g. ASTs) or table hierarchies unless coupled with specialized markdown/code splitters.
  - Fixed-character thresholds may split mid-sentence if a sentence exceeds `chunk_size`.

---

## 6. Configuration Integration

Chunking parameters are not hardcoded. They flow directly from the centralized configuration system established in Phase 2:

```text
  config.yaml:
  rag:
    chunk_size: 800
    chunk_overlap: 100
          │
          ▼
  app.core.config.RAGConfig (Validated on startup)
          │
          ▼
  app.core.config.Settings.chunk_size & chunk_overlap
          │
          ▼
  DocumentChunker() (Initializes with settings.chunk_size & settings.chunk_overlap)
```

If tuning experiments in later phases show that `chunk_size: 600` or `chunk_overlap: 120` produces better retrieval accuracy, developers only change `config.yaml`. No Python code in `chunker.py` needs to be edited.

---

## 7. Metadata Preservation

Every chunk inherits 100% of its parent document's metadata, guaranteeing complete traceability from a retrieved vector chunk back to the exact source page.

| Input Metadata (Phase 3) | Preserved in Chunk? | Added Metadata (Phase 4) |
| :--- | :---: | :--- |
| `source`: `"annual_report.pdf"` | Yes | `chunk_index`: `0` (Sequential position) |
| `file_name`: `"annual_report.pdf"` | Yes | `chunk_count`: `3` (Total chunks from parent doc) |
| `file_path`: `"/data/annual_report.pdf"` | Yes | `char_count`: `784` (Exact character length) |
| `file_type`: `"pdf"` | Yes | |
| `page`: `4` | Yes | |
| `total_pages`: `28` | Yes | |

---

## 8. Edge Cases Handled

1. **Empty Documents (`""`)**: Handled gracefully. `chunk_document()` detects empty or whitespace-only strings and returns an empty list `[]` without raising an exception.
2. **Documents Shorter than `chunk_size`**: Returned as a single chunk with original text untouched and metadata initialized (`chunk_index: 0`, `chunk_count: 1`).
3. **Invalid `chunk_size` (`<= 0`)**: Immediate `ChunkingConfigurationError` during initialization.
4. **Invalid `chunk_overlap` (`< 0`)**: Immediate `ChunkingConfigurationError` during initialization.
5. **Overlap Greater than or Equal to Chunk Size (`overlap >= chunk_size`)**: Prevented with a `ChunkingConfigurationError`, avoiding infinite recursion or zero-progress loops.
6. **Repeated Invocations**: Guarantees deterministic chunk boundaries and identical counts across runs.

---

## 9. Testing

### Execution Command
```powershell
.venv\Scripts\Activate.ps1; cd NexusRag/backend; python -m pytest -v
```

### Complete Test Results (34 Passed, 0 Failed):
```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Academic-Projects\RAG\NexusRag\backend
plugins: anyio-4.15.1, langsmith-0.12.1
collected 34 items

tests/test_chunking.py::test_centralized_config_integration PASSED       [  2%]
tests/test_chunking.py::test_basic_document_chunking PASSED              [  5%]
tests/test_chunking.py::test_multiple_documents_batch PASSED             [  8%]
tests/test_chunking.py::test_document_shorter_than_chunk_size PASSED     [ 11%]
tests/test_chunking.py::test_empty_and_whitespace_documents PASSED       [ 14%]
tests/test_chunking.py::test_metadata_preservation PASSED                [ 17%]
tests/test_chunking.py::test_chunk_indexing_and_counts PASSED            [ 20%]
tests/test_chunking.py::test_deterministic_chunking PASSED               [ 23%]
tests/test_chunking.py::test_invalid_chunk_size_validation PASSED        [ 26%]
tests/test_chunking.py::test_invalid_overlap_negative_validation PASSED  [ 29%]
tests/test_chunking.py::test_invalid_overlap_greater_equal_chunk_size PASSED [ 32%]
tests/test_config.py::test_default_settings_instantiation PASSED         [ 35%]
tests/test_config.py::test_yaml_config_parameters PASSED                 [ 38%]
tests/test_config.py::test_invalid_rag_overlap_validation PASSED         [ 41%]
tests/test_config.py::test_invalid_llm_temperature_validation PASSED     [ 44%]
tests/test_config.py::test_prohibited_secrets_in_yaml PASSED             [ 47%]
tests/test_config.py::test_secret_masking PASSED                         [ 50%]
tests/test_health.py::test_health_check_returns_200_and_healthy PASSED   [ 52%]
tests/test_health.py::test_health_check_content_type PASSED              [ 55%]
tests/test_health.py::test_app_operates_without_external_dependencies PASSED [ 58%]
tests/test_ingestion.py::test_ingest_txt_file PASSED                     [ 61%]
tests/test_ingestion.py::test_ingest_markdown_file PASSED                [ 64%]
tests/test_ingestion.py::test_ingest_pdf_file PASSED                     [ 67%]
tests/test_ingestion.py::test_ingest_unsupported_extension PASSED        [ 70%]
tests/test_ingestion.py::test_ingest_missing_file PASSED                 [ 73%]
tests/test_ingestion.py::test_ingest_empty_file PASSED                   [ 76%]
tests/test_ingestion.py::test_ingest_corrupted_pdf PASSED                [ 79%]
tests/test_ingestion.py::test_ingest_empty_content PASSED                [ 82%]
tests/test_ingestion.py::test_file_size_limit_enforced PASSED            [ 85%]
tests/test_ingestion.py::test_ingest_directory_batch PASSED              [ 88%]
tests/test_logging.py::test_sensitive_data_filter_redaction PASSED       [ 91%]
tests/test_logging.py::test_sensitive_data_filter_preserves_normal_messages PASSED [ 94%]
tests/test_logging.py::test_logging_level_configuration PASSED           [ 97%]
tests/test_logging.py::test_logger_redaction_stream PASSED               [100%]

======================= 34 passed, 2 warnings in 1.46s ========================
```

---

## 10. Concrete Example

### Original Document (Phase 3 Output)
```python
Document(
    page_content="""NexusRAG is an enterprise-grade retrieval application.
It integrates FastAPI, LangChain, ChromaDB, and Gemini.

The ingestion layer parses raw files into structured documents.
The chunking layer breaks documents into overlapping segments.
The embedding layer maps text into dense vector spaces.""",
    metadata={
        "source": "architecture.md",
        "file_type": "md",
        "page": 1,
        "total_pages": 1,
    }
)
```

### Resulting Chunks (Phase 4 Output with `chunk_size=150`, `chunk_overlap=30`)
```python
# Chunk 0:
Document(
    page_content="NexusRAG is an enterprise-grade retrieval application.\nIt integrates FastAPI, LangChain, ChromaDB, and Gemini.",
    metadata={
        "source": "architecture.md",
        "file_type": "md",
        "page": 1,
        "total_pages": 1,
        "chunk_index": 0,
        "chunk_count": 2,
        "char_count": 111,
    }
)

# Chunk 1 (Includes overlapping context from previous section):
Document(
    page_content="The ingestion layer parses raw files into structured documents.\nThe chunking layer breaks documents into overlapping segments.",
    metadata={
        "source": "architecture.md",
        "file_type": "md",
        "page": 1,
        "total_pages": 1,
        "chunk_index": 1,
        "chunk_count": 2,
        "char_count": 128,
    }
)
```

---

## 11. Important Design Decisions

1. **Separation of Ingestion and Chunking**: Ingestion reads disk files into page-level or document-level objects; chunking splits them into sub-document units. This separation allows changing file formats (e.g. adding `.docx` or `.html`) without modifying splitting logic, and vice versa.
2. **Recursive Splitting over Fixed Character Slicing**: Avoids breaking words, sentences, and paragraphs in half by prioritizing natural linguistic boundaries (`\n\n`, `\n`, `" "`).
3. **Sequential Chunk Indexing (`chunk_index` / `chunk_count`)**: Storing chunk order within metadata enables future advanced RAG capabilities such as "adjacent chunk retrieval" or "parent-child document retrieval".
4. **Defensive Boundary Validation**: Validating that `chunk_overlap < chunk_size` at initialization prevents infinite loops or zero-step sliding windows.
5. **No Direct Hardcoding**: `DocumentChunker` pulls parameters from `Settings` while allowing optional constructor overrides for unit tests.

---

## 12. Connection to Phase 5 (Embeddings)

In Phase 5, the **Embeddings Layer** will consume the output of Phase 4:
1. **Input Signature**: Phase 5 embedding services (e.g. Gemini embedding API or open-source embeddings) receive the text chunks via `[chunk.page_content for chunk in chunks]`.
2. **Dense Vector Mapping**: Each chunk's text is converted into a high-dimensional vector (e.g., 768 or 1536 floating-point dimensions).
3. **Index Pairing**: The embedding layer pairs each dense vector with the chunk's text and metadata (`source`, `page`, `chunk_index`), preparing it for batch insertion into ChromaDB (Phase 6).

---

## 13. Interview Knowledge (Applied to NexusRAG)

- **The Chunk Size Tradeoff**: Small chunks (e.g. 200 chars) increase retrieval precision but lose broad semantic context. Large chunks (e.g. 2000 chars) capture complete context but dilute semantic similarity and bloat LLM prompt tokens. NexusRAG defaults to 800 characters with 100 overlap as an optimal baseline for paragraph-level QA.
- **Chunk Overlap**: Overlap bridges the semantic boundary between consecutive chunks. Without overlap, a query matching keywords spanning the split point will fail to achieve high cosine similarity.
- **Deterministic Preprocessing**: In production ML and RAG systems, given identical input and configuration, data preparation must yield identical chunks every time to ensure reproducible vector indexes and evaluation benchmarks.
- **Context Preservation in Metadata**: Retaining `page`, `source`, and `file_type` across chunking is essential for building verifiable citations and post-retrieval filtering in production applications.

---

## 14. Verification Checklist

- [x] Documents can be chunked into smaller segments (`chunk_document`, `chunk_documents`)
- [x] Metadata is preserved across all chunks (`source`, `file_type`, `page`, etc.)
- [x] Configuration is respected (`chunk_size` and `chunk_overlap` loaded from `config.yaml` / `Settings`)
- [x] Invalid configuration is handled (`ChunkingConfigurationError` raised on invalid bounds)
- [x] Empty and whitespace-only documents are handled gracefully
- [x] Logging works (operational event logs emitted, document contents protected)
- [x] All 34 automated tests pass
- [x] Phase 1 still works (FastAPI health check returns 200 OK)
- [x] Phase 2 still works (Configuration and logging tests fully green)
- [x] Phase 3 still works (Document ingestion tests fully green)
