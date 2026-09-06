# Phase 3 — Document Ingestion

## 1. Objective

The objective of Phase 3 is to implement the **Document Ingestion Layer** for **NexusRAG**. In a production Retrieval-Augmented Generation (RAG) system, raw files cannot be directly fed into vector stores or LLM contexts. Instead, documents must first undergo rigorous validation, format-specific extraction, text normalization, and metadata standardization to produce structured LangChain `Document` objects.

This phase acts as the ingestion boundary of NexusRAG:
- Validates input files (preventing empty, oversized, unsupported, or corrupted files from entering the pipeline).
- Parses multiple file formats (PDF, plain text, Markdown) into standardized text representations.
- Attaches essential metadata (e.g. source file name, file type, page number, file size) required for source attribution and citations in downstream RAG responses.
- Provides a clean, reusable interface (`DocumentService`) that will feed directly into Phase 4 (document chunking).

---

## 2. Files Created / Modified

| File | Purpose | Changes |
| :--- | :--- | :--- |
| `backend/app/ingestion/loader.py` | Format-specific loading and extraction | Created `BaseDocumentLoader`, `PDFDocumentLoader` (using `PyPDFLoader`), `TextDocumentLoader`, `MarkdownDocumentLoader`, and `DocumentLoaderFactory`. Implemented custom ingestion exception hierarchy. Added text cleaning and metadata normalization. |
| `backend/app/ingestion/document_service.py` | Ingestion orchestration and validation | Created `DocumentService` with pre-flight file validation (`validate_file`), single file ingestion (`ingest_file`), directory batch ingestion (`ingest_directory`), and structured logging. |
| `backend/app/ingestion/__init__.py` | Module exports | Cleanly exposed `DocumentService`, loaders, and custom exception classes. |
| `backend/app/core/config.py` | Ingestion configuration integration | Added `IngestionConfig` submodel (`max_file_size_mb`, `allowed_extensions`) and convenience properties (`max_file_size_bytes`, `allowed_extensions`) to `Settings`. |
| `backend/config.yaml` | Non-secret parameter storage | Added `ingestion` configuration block defining maximum file size (10 MB) and permitted extensions (`.pdf`, `.txt`, `.md`). |
| `backend/requirements.txt` | Dependency declaration | Added `langchain-core>=0.3.0`, `langchain-community>=0.3.0`, and `pypdf>=5.0.0`. |
| `backend/tests/test_ingestion.py` | Ingestion test suite | Created 10 test cases covering PDF, TXT, and MD ingestion, missing files, empty files, corrupted PDFs, blank content, size limit enforcement, directory batching, and metadata preservation. |

---

## 3. Ingestion Architecture

The ingestion pipeline follows a strict unidirectional processing pipeline:

```text
       Uploaded / Provided File Path
                     │
                     ▼
          Pre-flight File Validation
       (Exists? Is file? Extension? Size?)
                     │
                     ▼
           DocumentLoaderFactory
       (Inspects suffix → selects Loader)
                     │
                     ▼
           Format-Specific Loader
      (PyPDFLoader / TextLoader with UTF-8 / Latin-1)
                     │
                     ▼
          Text Sanitization & Cleanup
     (Strip null bytes, normalize \r\n, collapse blank lines)
                     │
                     ▼
          Metadata Normalization
  (source, file_name, file_path, file_type, page, total_pages, file_size)
                     │
                     ▼
            Content Verification
      (Ensures non-empty extractable text exists)
                     │
                     ▼
         List[LangChain Document]
                     │
                     ▼
       Ready for Phase 4: Chunking
```

---

## 4. File-by-File Walkthrough

### `backend/app/ingestion/loader.py`
- **Responsibility**: Houses format-specific parsing logic, sanitization utilities, custom exceptions, and the loader factory.
- **Key Classes & Functions**:
  - `IngestionError`: Base exception for all ingestion failures.
  - Specific Exceptions: `FileNotFoundIngestionError`, `UnsupportedFileTypeError`, `EmptyFileError`, `FileTooLargeError`, `CorruptedFileError`, `EmptyContentError`.
  - `BaseDocumentLoader`: Abstract base class enforcing `load(file_path: Path) -> List[Document]`. Includes `clean_text(text: str) -> str` which strips null bytes (`\x00`), standardizes carriage returns (`\r\n` and `\r` to `\n`), and collapses redundant whitespace lines.
  - `PDFDocumentLoader`: Employs `PyPDFLoader` from `langchain_community`. Converts 0-indexed PDF pages to 1-indexed pages for citations. Catches PDF syntax errors and raises `CorruptedFileError`.
  - `TextDocumentLoader` & `MarkdownDocumentLoader`: Employ `TextLoader` with an automated fallback strategy (tries `utf-8` first, falls back to `latin-1` if decoding errors occur).
  - `DocumentLoaderFactory`: Factory registry resolving `.pdf`, `.txt`, and `.md` extensions to their respective loader instances.
- **Dependencies**: `langchain_core.documents.Document`, `langchain_community.document_loaders`, `pypdf`.
- **Interaction**: Called directly by `DocumentService`.

### `backend/app/ingestion/document_service.py`
- **Responsibility**: Orchestrates pre-flight validation, loader delegation, post-extraction verification, and batch processing.
- **Key Classes & Functions**:
  - `DocumentService(settings: Optional[Settings] = None)`: Injects configuration (defaulting to `get_settings()`).
  - `validate_file(file_path: Path) -> None`: Validates existence, regular file status, allowed extension (`settings.allowed_extensions`), 0-byte check, and file size limits (`settings.max_file_size_bytes`).
  - `ingest_file(file_path: str | Path) -> List[Document]`: Validates the file, obtains the appropriate loader, extracts documents, verifies that extractable non-whitespace text exists, and returns the standardized list.
  - `ingest_directory(directory_path: str | Path, recursive: bool = False) -> List[Document]`: Scans a directory for matching extensions and aggregates extracted documents while logging warnings for individual failed files.
- **Error Handling**: Catches domain exceptions (`IngestionError` hierarchy) and logs warnings. Unanticipated system exceptions are caught and wrapped into an `IngestionError` with contextual details.
- **Interaction**: Consumed by future API endpoints (Phase 11) or CLI scripts to feed documents into the Phase 4 chunker.

### `backend/app/ingestion/__init__.py`
- **Responsibility**: Package public API. Exports `DocumentService`, loaders, and all custom exception classes for clean external imports.

### `backend/app/core/config.py` & `backend/config.yaml`
- **Responsibility**: Manages ingestion constraints without hardcoded constants.
- **Settings Added**:
  - `IngestionConfig`: `max_file_size_mb: int = 10`, `allowed_extensions: List[str] = [".pdf", ".txt", ".md"]`.
  - Properties: `max_file_size_bytes` (MB converted to bytes) and `allowed_extensions`.
  - Stored in `config.yaml` under the `ingestion` block.

### `backend/tests/test_ingestion.py`
- **Responsibility**: Exhaustive automated verification of the ingestion pipeline across successful parsing, edge cases, and failure scenarios.

---

## 5. Supported Formats

| Format | Extension | Loader Implementation | Handling Details |
| :--- | :---: | :--- | :--- |
| **PDF** | `.pdf` | `PDFDocumentLoader` via `PyPDFLoader` | Reads page-by-page. Normalizes 0-indexed page numbers to 1-indexed for citation transparency. Records `total_pages`. Traps corrupted streams and invalid xref tables as `CorruptedFileError`. |
| **Plain Text** | `.txt` | `TextDocumentLoader` via `TextLoader` | Reads raw text with UTF-8 priority, falling back to Latin-1 encoding to prevent decoding crashes. Sets `page: 1` and `total_pages: 1`. |
| **Markdown** | `.md` | `MarkdownDocumentLoader` via `TextLoader` | Preserves headers, bullet points, and code blocks intact for structural chunking in Phase 4. Sets `page: 1` and `total_pages: 1`. |

---

## 6. Metadata Design for RAG Source Attribution

In a production RAG application, generating an answer without verifiable citations reduces user trust and makes auditing impossible. Every LangChain `Document` produced by the ingestion layer contains standardized metadata fields:

```json
{
  "source": "annual_report.pdf",
  "file_name": "annual_report.pdf",
  "file_path": "/var/data/documents/annual_report.pdf",
  "file_type": "pdf",
  "page": 4,
  "total_pages": 28,
  "file_size_bytes": 1048576
}
```

### Why Each Field Matters:
1. **`source`**: The primary reference used in citation strings returned by the RAG pipeline (e.g. *"[Source: annual_report.pdf, Page 4]"*).
2. **`file_name`**: The clean basename of the file, decoupling citations from host directory structures.
3. **`file_path`**: Absolute filesystem path allowing future retrieval services to locate or re-read original documents.
4. **`file_type`**: Enables downstream filtering (e.g., restricting a retrieval query to PDF policies vs. Markdown notes).
5. **`page`**: The 1-indexed page number. In PDF documents, this allows the user interface to jump directly to the referenced page.
6. **`total_pages`**: Contextual awareness of document length.
7. **`file_size_bytes`**: Telemetry and data auditing.

---

## 7. Error Handling

The ingestion pipeline detects and cleanly handles all major document failure scenarios:

| Failure Case | Detected Condition | Exception Raised | HTTP Mapping (Future API) |
| :--- | :--- | :--- | :--- |
| **Non-existent file** | `not path.exists()` | `FileNotFoundIngestionError` | `404 Not Found` |
| **Directory as file** | `not path.is_file()` | `FileNotFoundIngestionError` | `400 Bad Request` |
| **Unsupported extension** | `suffix not in allowed_extensions` | `UnsupportedFileTypeError` | `415 Unsupported Media Type` |
| **Zero-byte file** | `path.stat().st_size == 0` | `EmptyFileError` | `400 Bad Request` |
| **File too large** | `file_size > max_file_size_bytes` | `FileTooLargeError` | `413 Payload Too Large` |
| **Corrupted PDF** | Malformed headers, unreadable xref | `CorruptedFileError` | `422 Unprocessable Entity` |
| **Blank / Scanned PDF** | No non-whitespace characters extracted | `EmptyContentError` | `422 Unprocessable Entity` |

---

## 8. Logging

Logging is integrated using the centralized logging system built in Phase 2 (`app.core.logging.get_logger(__name__)`).

### What Is Logged:
- Ingestion start with file basename: `Ingestion started for document: 'hr_policy.pdf'`
- Format identification: `Detected file format '.pdf' for 'hr_policy.pdf'`
- Success summary: `Ingestion completed for 'hr_policy.pdf': successfully extracted 4 document/page item(s)`
- Batch progress: `Directory scan finished for '/data/docs': 12 total document items ingested`
- Validation warnings: `Ingestion rejected for 'report.docx': File extension '.docx' is not supported.`

### What Is Deliberately NOT Logged:
- Raw document text (protects confidential user data, PII, and sensitive business text).
- Host authorization tokens, cookies, or secrets.
- Full unformatted stack traces in production warning logs.

---

## 9. Testing

### Test Suite Execution
Tests were executed in the project virtual environment using `pytest`:

```powershell
.venv\Scripts\Activate.ps1; cd NexusRag/backend; python -m pytest -v
```

### Complete Test Results (23 Passed, 0 Failed):
```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Academic-Projects\RAG\NexusRag\backend
plugins: anyio-4.15.1, langsmith-0.12.1
collected 23 items

tests/test_config.py::test_default_settings_instantiation PASSED         [  4%]
tests/test_config.py::test_yaml_config_parameters PASSED                 [  8%]
tests/test_config.py::test_invalid_rag_overlap_validation PASSED         [ 13%]
tests/test_config.py::test_invalid_llm_temperature_validation PASSED     [ 17%]
tests/test_config.py::test_prohibited_secrets_in_yaml PASSED             [ 21%]
tests/test_config.py::test_secret_masking PASSED                         [ 26%]
tests/test_health.py::test_health_check_returns_200_and_healthy PASSED   [ 30%]
tests/test_health.py::test_health_check_content_type PASSED              [ 34%]
tests/test_health.py::test_app_operates_without_external_dependencies PASSED [ 39%]
tests/test_ingestion.py::test_ingest_txt_file PASSED                     [ 43%]
tests/test_ingestion.py::test_ingest_markdown_file PASSED                [ 47%]
tests/test_ingestion.py::test_ingest_pdf_file PASSED                     [ 52%]
tests/test_ingestion.py::test_ingest_unsupported_extension PASSED        [ 56%]
tests/test_ingestion.py::test_ingest_missing_file PASSED                 [ 60%]
tests/test_ingestion.py::test_ingest_empty_file PASSED                   [ 65%]
tests/test_ingestion.py::test_ingest_corrupted_pdf PASSED                [ 69%]
tests/test_ingestion.py::test_ingest_empty_content PASSED                [ 73%]
tests/test_ingestion.py::test_file_size_limit_enforced PASSED            [ 78%]
tests/test_ingestion.py::test_ingest_directory_batch PASSED              [ 82%]
tests/test_logging.py::test_sensitive_data_filter_redaction PASSED       [ 86%]
tests/test_logging.py::test_sensitive_data_filter_preserves_normal_messages PASSED [ 91%]
tests/test_logging.py::test_logging_level_configuration PASSED           [ 95%]
tests/test_logging.py::test_logger_redaction_stream PASSED               [100%]

======================= 23 passed, 2 warnings in 1.41s ========================
```

---

## 10. Data Flow

```text
  [ Client / Local Filesystem ]
               │
               ▼
   DocumentService.ingest_file(path)
               │
   ┌───────────┴───────────┐
   ▼                       ▼
Validation Checks:       DocumentLoaderFactory.get_loader(path)
- File exists?                   │
- Is regular file?               ├─► .pdf ──► PDFDocumentLoader (PyPDF)
- Suffix allowed?                ├─► .txt ──► TextDocumentLoader (UTF-8/Latin-1)
- Size > 0 & <= 10MB?            └─► .md  ──► MarkdownDocumentLoader (UTF-8/Latin-1)
   │                               │
   └───────────────┬───────────────┘
                   │
                   ▼
       Format Loader Execution
                   │
                   ▼
     Text Sanitization (clean_text)
- Strip null characters
- Normalize line endings to \n
- Collapse blank lines
                   │
                   ▼
     Metadata Construction
- source, file_name, file_path, file_type
- page (1-indexed), total_pages, file_size_bytes
                   │
                   ▼
     Extractable Content Validation
- Check: non-whitespace content present?
                   │
                   ▼
       List[Document] Returned
```

---

## 11. Connection to Phase 4 (Document Chunking)

In Phase 4, the **Chunking Layer** will take the output of Phase 3 as its direct input:
1. **Input Signature**: Phase 4 text splitters (e.g., `RecursiveCharacterTextSplitter`) accept `List[Document]`.
2. **Metadata Propagation**: When a Document is split into chunks, LangChain copies the document's metadata to every resulting chunk, adding chunk index and token span metadata.
3. **Hyperparameters**: The chunker will consume `settings.chunk_size` (800) and `settings.chunk_overlap` (100) established in Phase 2.
4. **Clean Input Guarantee**: Phase 4 never has to worry about 0-byte files, unreadable binary PDFs, or encoding exceptions because Phase 3 guarantees clean, validated `Document` objects.

---

## 12. Interview Knowledge (Applied to NexusRAG)

- **Factory Pattern (`DocumentLoaderFactory`)**: Encapsulates object creation based on file extensions. Adding support for a new format (e.g. `.docx`) requires implementing a new loader and registering it in the factory without modifying consumer code (Open/Closed Principle).
- **Graceful Encoding Degradation**: Files created on Windows often use `cp1252` / `latin-1` rather than `utf-8`. Hardcoding UTF-8 crashes on standard corporate documents. Trying UTF-8 and falling back to Latin-1 guarantees resilient text reading.
- **Fail-Fast Validation**: Validating file size, existence, and format *before* invoking expensive parser libraries prevents resource exhaustion (DoS) and reduces latency.
- **Separation of Ingestion and Chunking**: Chunking algorithms change frequently (fixed-size, semantic, sentence-window). Keeping ingestion separate from chunking ensures loader improvements do not affect text splitting logic.
- **Structured Metadata for Citation**: In production RAG, an LLM answer is only as good as its source attribution. Capturing 1-indexed page numbers during ingestion enables source verification in the final user interface.

---

## 13. Verification Checklist

- [x] PDF ingestion works (tested with text-bearing PDF)
- [x] TXT ingestion works (tested with UTF-8 text file)
- [x] Markdown ingestion works (tested with formatted Markdown)
- [x] Metadata is preserved (`source`, `file_type`, `page`, `total_pages`, `file_size_bytes`)
- [x] Invalid files are handled (unsupported extensions, missing files, 0-byte files, corrupted PDFs, blank files)
- [x] Logging works (structured logs emitted, zero sensitive document text or keys leaked)
- [x] Tests pass (23/23 tests passing)
- [x] Phase 1 still works (FastAPI health endpoint verified returning HTTP 200 with `{"status": "healthy"}`)
- [x] Phase 2 still works (configuration and logging tests fully green, dynamic YAML parameters loaded)
