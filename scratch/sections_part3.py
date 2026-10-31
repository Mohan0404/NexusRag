"""
Part III Generator for NexusRAG Handbook: Document Ingestion, Embeddings, and ChromaDB.
"""

def generate_part_3(builder):
    b = builder
    html_out = []

    # Part III Divider
    topics = [
        {"title": "09. Ingestion Pipeline Architecture", "desc": "Nine-stage transformation from raw file upload to searchable vector embeddings."},
        {"title": "10. Document Loaders & Format Parsing", "desc": "Format-specific parsing with PyPDFLoader and TextLoader, plus extension whitelists."},
        {"title": "11. Text Sanitization & Normalization", "desc": "Whitespace collapse, control character cleaning, and zero-extractable-content guards."},
        {"title": "12. Recursive Character Chunking Strategy", "desc": "Why 800 chunk size and 100 character overlap preserve semantic context boundaries."},
        {"title": "13. Metadata Architecture & Isolation", "desc": "Strict tracking of source, page, chunk_index, and ISO8601 indexed_at timestamps."},
        {"title": "14. Gemini Embedding 2 Deep Dive", "desc": "768-dimensional dense vectors, batching optimizations, and Matryoshka dimension overrides."},
        {"title": "15. ChromaDB Vector Store Architecture", "desc": "PersistentClient configuration, SQLite metadata management, and HNSW Euclidean index."}
    ]
    html_out.append(b.build_part_divider(
        roman="III",
        title="DOCUMENT → KNOWLEDGE BASE",
        quote="How NexusRAG transforms unstructured corporate files into structured, searchable dense vector knowledge.",
        topics=topics
    ))

    # Section 09: Ingestion Pipeline Architecture (Figure B)
    html_out.append(b.build_section_header(
        num_str="09",
        title="Document Ingestion Pipeline Architecture",
        summary="Nine-stage data transformation pipeline converting raw multi-format files into dense vector embeddings.",
        sec_id="sec-09"
    ))

    html_out.append(b.build_diagram_box(
        fig_num="B",
        title="Nine-Stage Document Ingestion & Vector Indexing Pipeline",
        svg_name="diagram_b_ingestion_pipeline.svg",
        what="End-to-end ingestion pipeline tracing a file from client upload through validation, staging, loading, text sanitization, recursive splitting, metadata injection, batch embedding, and ChromaDB persistence.",
        how="Files are validated and staged to isolated disk paths. PyPDFLoader or TextLoader extracts raw text. Text is sanitized and split into 800-character chunks with 100-character overlap. GeminiEmbeddingService generates 768-dim embeddings in batches of 100, which are upserted to ChromaDB before purging Redis.",
        why="Staging files to unique UUID paths prevents race conditions between simultaneous uploads. Ingesting and embedding before cache invalidation ensures queries never serve stale answers.",
        interview_point="Staged files are unlinked in a finally block regardless of success or failure, guaranteeing zero disk leaks during upload errors."
    ))

    # Section 10: Document Loaders & Format Parsing
    html_out.append(b.build_section_header(
        num_str="10",
        title="Document Loaders & Format-Specific Parsing",
        summary="Format-specific parsers supporting PDF, TXT, and Markdown files with strict extension whitelisting.",
        sec_id="sec-10"
    ))

    html_out.append("""
    <div class="content-block">
      <h3>10.1 Loader Selection &amp; Strategy</h3>
      <p>
        NexusRAG supports three primary corporate document formats using dedicated parser wrappers inside <code>backend/app/ingestion/loader.py</code>:
      </p>
      <table>
        <thead>
          <tr>
            <th>Format</th>
            <th>Parser Implementation</th>
            <th>Metadata Extracted</th>
            <th>Handling of Special Elements</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Portable Document Format (.pdf)</strong></td>
            <td><code>langchain_community.document_loaders.PyPDFLoader</code></td>
            <td><code>page: int</code> (1-indexed), <code>source: str</code></td>
            <td>Extracts native text streams page-by-page. Scanned image-only PDFs yield 0 characters and trigger HTTP 422.</td>
          </tr>
          <tr>
            <td><strong>Plain Text (.txt)</strong></td>
            <td><code>langchain_community.document_loaders.TextLoader</code></td>
            <td><code>source: str</code>, <code>page: 1</code> (synthetic)</td>
            <td>Decodes UTF-8 text directly; strips BOM markers; handles standard CRLF/LF line endings.</td>
          </tr>
          <tr>
            <td><strong>Markdown (.md)</strong></td>
            <td><code>langchain_community.document_loaders.TextLoader</code></td>
            <td><code>source: str</code>, <code>page: 1</code> (synthetic)</td>
            <td>Preserves header hashes, bullet points, and code blocks for semantic chunk boundary splitting.</td>
          </tr>
        </tbody>
      </table>

      <h3>10.2 File Validation Rules</h3>
      <ul>
        <li><strong>Extension Whitelist:</strong> Only <code>.pdf</code>, <code>.txt</code>, and <code>.md</code> are permitted. Unrecognized extensions (e.g., <code>.exe</code>, <code>.docx</code>, <code>.zip</code>) immediately return HTTP 400.</li>
        <li><strong>Size Limit Enforcement:</strong> Files exceeding <code>max_file_size_mb = 10</code> are rejected before disk buffering with HTTP 413.</li>
        <li><strong>Zero-Byte Rejection:</strong> Files with 0 bytes or zero extractable text content return HTTP 422 Unprocessable Entity.</li>
      </ul>
    </div>
    """)

    # Section 11: Text Sanitization & Normalization
    html_out.append(b.build_section_header(
        num_str="11",
        title="Text Sanitization & Normalization",
        summary="Pre-chunking text cleaning to eliminate non-printable artifacts, trailing spaces, and excessive whitespace.",
        sec_id="sec-11"
    ))

    html_out.append("""
    <div class="content-block">
      <p>
        Extracted raw text often contains layout artifacts, inconsistent newline sequences, and redundant whitespace that inflate token counts and distort embedding vectors. The helper function <code>helpers.clean_text()</code> applies deterministic sanitization rules:
      </p>
      <pre><code>def clean_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    # Strip leading/trailing whitespace
    text = raw_text.strip()
    # Normalize multiple newlines to double newlines (paragraph preservation)
    text = re.sub(r'\\n{3,}', '\\n\\n', text)
    # Collapse consecutive horizontal whitespace (spaces/tabs) to a single space
    text = re.sub(r'[ \\t]+', ' ', text)
    return text</code></pre>
      <div class="callout callout-info no-break">
        <div class="callout-header"><span>ℹ️</span> WHY CLEAN TEXT BEFORE CHUNKING?</div>
        <p>
          Whitespace characters consume embedding tokens without contributing semantic meaning. Collapsing multiple spaces and non-standard newlines ensures that the 800-character chunk window is densely packed with informative semantic tokens.
        </p>
      </div>
    </div>
    """)

    # Section 12: Recursive Character Chunking Strategy
    html_out.append(b.build_section_header(
        num_str="12",
        title="Recursive Character Chunking Strategy",
        summary="Hierarchical text splitting maintaining natural paragraph, sentence, and word boundaries with context overlap.",
        sec_id="sec-12"
    ))

    html_out.append("""
    <div class="content-block">
      <h3>12.1 Why Recursive Character Text Splitting?</h3>
      <p>
        Fixed-character chunking arbitrarily cuts sentences and words in half, destroying grammatical and semantic cohesion. NexusRAG employs LangChain's <code>RecursiveCharacterTextSplitter</code> with a hierarchical list of separators:
      </p>
      <pre><code>separators = ["\\n\\n", "\\n", " ", ""]</code></pre>
      <p>
        The splitter attempts to split at double newlines (paragraphs) first. If a paragraph exceeds 800 characters, it falls back to single newlines (lines), then spaces (words), and only splits mid-character as a last resort.
      </p>

      <h3>12.2 Hyperparameter Defense: Why 800 Characters and 100 Overlap?</h3>
      <table>
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Config Value</th>
            <th>Engineering Rationale</th>
            <th>Trade-Off Analyzed</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>chunk_size</code></td>
            <td><strong>800 characters</strong> (~150–200 tokens)</td>
            <td>Provides complete semantic units (2–3 full sentences or a concise paragraph) without diluting the specific focal topic of the chunk.</td>
            <td>Larger chunks (1500+) dilute specific facts in average vector pooling; smaller chunks (300) lose contextual pronouns and subjects.</td>
          </tr>
          <tr>
            <td><code>chunk_overlap</code></td>
            <td><strong>100 characters</strong> (~20–25 tokens)</td>
            <td>Maintains semantic continuity across chunk boundaries, ensuring that entities or clauses split near the 800-character margin are not truncated from context.</td>
            <td>Increases total chunk count by ~12.5%, modestly increasing embedding API cost in exchange for boundary safety.</td>
          </tr>
        </tbody>
      </table>
    </div>
    """)

    # Section 13: Metadata Architecture
    html_out.append(b.build_section_header(
        num_str="13",
        title="Metadata Architecture & Document Isolation",
        summary="Per-chunk metadata schemas enforcing document identity, page provenance, and temporal ordering.",
        sec_id="sec-13"
    ))

    html_out.append("""
    <div class="content-block">
      <p>
        Every chunk stored in ChromaDB is paired with a strict JSON-serializable metadata dictionary. ChromaDB does not support nested JSON objects in metadata, so all attributes are flattened into primitive types:
      </p>
      <pre><code>metadata = {
    "source": "employee_handbook.pdf",  # Canonical clean filename (source of truth)
    "page": 4,                          # Page number (1-based integer for citation)
    "chunk_index": 12,                  # Deterministic sequential index within document
    "indexed_at": "2026-09-06T20:15:00Z"# ISO 8601 UTC timestamp of indexing
}</code></pre>
      <div class="callout callout-warning no-break">
        <div class="callout-header"><span>⚠️</span> METADATA SANITIZATION &amp; LEGACY UUID CANONICALIZATION</div>
        <p>
          During Phase 15, we discovered that older document uploads prepended a 32-character hexadecimal UUID to the filename (e.g., <code>f0bab8b4..._policy.pdf</code>). To prevent duplicate entries in the document list, <code>ChromaStore.list_sources()</code> implements regex canonicalization to strip legacy UUID prefixes, ensuring that physical chunk counts accurately represent the clean document name.
        </p>
      </div>
    </div>
    """)

    # Section 14: Google Gemini Embedding 2
    html_out.append(b.build_section_header(
        num_str="14",
        title="Embedding Service Deep Dive (Google Gemini Embedding 2)",
        summary="768-dimensional dense vector embeddings with batching optimizations and asymmetric task-type projection.",
        sec_id="sec-14"
    ))

    html_out.append("""
    <div class="content-block">
      <h3>14.1 Why Google Gemini Embedding 2?</h3>
      <p>
        NexusRAG selected Google's <code>gemini-embedding-2</code> (via the official <code>google-genai</code> SDK) as its primary embedding engine based on three technical justifications:
      </p>
      <ul>
        <li><strong>Native Multilingual &amp; Technical Density:</strong> Excels at enterprise documentation containing mixed prose, tabular data, code snippets, and acronyms.</li>
        <li><strong>768 Output Dimension:</strong> Provides higher semantic expressiveness than standard 384-dim open-source models while requiring 50% less memory and disk footprint than 1536-dim OpenAI models.</li>
        <li><strong>Matryoshka Representation Learning:</strong> Supports flexible dimension truncation without catastrophic loss of retrieval accuracy.</li>
      </ul>

      <h3>14.2 Batching Optimization &amp; Asymmetric Task Types</h3>
      <p>
        Embedding APIs incur significant HTTP round-trip latency if called per-chunk. <code>GeminiEmbeddingService</code> batches chunk embeddings in groups of 100 (<code>batch_size = 100</code>). A 35-page document producing 140 chunks is embedded in just 2 network calls rather than 140.
      </p>
      <p>
        Crucially, the embedder distinguishes between document chunks and user queries using asymmetric task types:
      </p>
      <ul>
        <li><strong>Documents:</strong> Embedded with task type <code>RETRIEVAL_DOCUMENT</code> (optimizes declarative passages).</li>
        <li><strong>Queries:</strong> Embedded with task type <code>RETRIEVAL_QUERY</code> (optimizes interrogative prompts).</li>
      </ul>
      <p>
        Asymmetric projection ensures questions and answers map into the same semantic neighborhood despite linguistic structural differences.
      </p>
    </div>
    """)

    # Section 15: Vector Database Architecture (ChromaDB)
    html_out.append(b.build_section_header(
        num_str="15",
        title="Vector Database Architecture (ChromaDB & ChromaStore)",
        summary="Persistent embedded vector database utilizing SQLite metadata catalog and HNSW index with Euclidean distance.",
        sec_id="sec-15"
    ))

    html_out.append("""
    <div class="content-block">
      <h3>15.1 ChromaStore Abstraction Layer</h3>
      <p>
        Directly coupling application routes to third-party vector store APIs creates fragile code that breaks on upstream version updates. NexusRAG implements <code>ChromaStore</code> (<code>backend/app/vectordb/chroma_store.py</code>) as an explicit domain abstraction over ChromaDB's <code>PersistentClient</code>.
      </p>
      <p>
        Key responsibilities of <code>ChromaStore</code> include:
      </p>
      <ul>
        <li><strong>Persistent Directory Binding:</strong> Automatically mounts local disk directory <code>./data/chroma_db</code> with SQLite storage.</li>
        <li><strong>Collection Isolation:</strong> Maintains all enterprise knowledge in a dedicated collection (<code>nexusrag_documents</code>).</li>
        <li><strong>Physical Record Source of Truth:</strong> Computes document chunk tallies by executing physical collection queries (<code>collection.get(where={"source": filename})</code>) rather than trusting cached metadata tags.</li>
        <li><strong>Deterministic Chunk ID Generation:</strong> Generates chunk IDs as <code>{source}_chunk_{index}</code> to ensure idempotency on repeated upserts.</li>
      </ul>

      <h3>15.2 Distance Metric: Euclidean Squared Distance (L2)</h3>
      <p>
        ChromaDB computes vector similarity using squared Euclidean distance ($L_2$ norm):
      </p>
      <p style="text-align: center; font-family: 'JetBrains Mono', monospace; font-size: 10pt; margin: 10pt 0;">
        d(u, v) = ∑ (u_i - v_i)²
      </p>
      <p>
        A distance of <code>0.0</code> indicates identical vectors, with smaller distances representing closer semantic proximity. Retrieved results are ranked in ascending order of distance, returning the closest Top-4 chunks to the RAG pipeline.
      </p>
    </div>
    """)

    return "".join(html_out)

print("Part III generator ready.")
