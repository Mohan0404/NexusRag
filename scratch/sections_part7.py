"""
Part VII Generator for NexusRAG Handbook: Engineering Decisions, Trade-offs, Limitations, and Roadmap.
"""

def generate_part_7(builder):
    b = builder
    html_out = []

    # Part VII Divider
    topics = [
        {"title": "37. Core Decisions & 10 Decision Cards", "desc": "Concrete justifications, trade-offs, and alternatives for all 10 core technologies."},
        {"title": "38. Comprehensive Trade-offs Matrix", "desc": "In-depth breakdown of 8 critical architectural compromises and their production evolutions."},
        {"title": "39. Architectural Limitations & Known Constraints", "desc": "Honest appraisal of current weaknesses: single collection, lack of auth, no OCR."},
        {"title": "40. Advanced RAG Evolution (V1 to V7)", "desc": "Phased roadmap from Dense Retrieval through Hybrid Search, Reranking, and Graph RAG."},
        {"title": "41. RAGAS Quality Evaluation Framework", "desc": "The RAG Triad: Faithfulness, Answer Relevance, Context Precision, and Recall."}
    ]
    html_out.append(b.build_part_divider(
        roman="VII",
        title="ENGINEERING JUDGEMENT",
        quote="Defending technical decisions, analyzing compromises, evaluating RAG quality, and laying out the future roadmap.",
        topics=topics
    ))

    # Section 37: Core Architectural Decisions & 10 Decision Cards
    html_out.append(b.build_section_header(
        num_str="37",
        title="Core Architectural Decisions & Technology Selection (10 Cards)",
        summary="Concrete defense for each chosen technology, alternatives rejected, trade-offs accepted, and when to change.",
        sec_id="sec-37"
    ))

    # Decision Card 1: React 18 & Vite
    html_out.append(b.build_decision_card(
        title="Why React 18 & Vite?",
        decision="Client-side React 18 SPA bundled with Vite.",
        rationale_list=[
            "NexusRAG is an internal enterprise tool, not an e-commerce site requiring SEO or SSR hydration overhead.",
            "Vite provides near-instant Hot Module Replacement (HMR) and simple static build output.",
            "Client-side SPA architecture decouples frontend completely from the Python backend."
        ],
        tradeoff="Requires client to download JavaScript bundle before rendering; initial page load depends on client device performance.",
        alternative="Next.js App Router / Remix",
        when_to_change="If NexusRAG becomes a public-facing documentation hub requiring search engine crawler indexing and OpenGraph social previews."
    ))

    # Decision Card 2: FastAPI
    html_out.append(b.build_decision_card(
        title="Why FastAPI?",
        decision="FastAPI running on Uvicorn ASGI with Python 3.11+.",
        rationale_list=[
            "Asynchronous event loop handles high-concurrency I/O (model API gateways, vector database queries) with minimal memory overhead.",
            "Built-in Pydantic integration enforces strict runtime data contracts and automated OpenAPI documentation.",
            "First-class dependency injection system enables clean singleton lifespans and painless test doubles."
        ],
        tradeoff="Async execution requires careful handling of blocking code (sync I/O must be routed to AnyIO thread pools).",
        alternative="Flask (Sync) or Django (Full-stack)",
        when_to_change="Never for this API tier; would only supplement with Go/Rust microservices if raw throughput exceeds 50,000 req/sec."
    ))

    # Decision Card 3: LangChain
    html_out.append(b.build_decision_card(
        title="Why LangChain Core?",
        decision="LangChain document loaders, recursive text splitters, and ChatOpenAI client.",
        rationale_list=[
            "Avoids reinventing battle-tested document parsing and boundary-aware recursive chunking algorithms.",
            "Provides standardized Document schema (page_content + metadata dict).",
            "Used purely as a library of utilities rather than an opaque, all-in-one execution chain."
        ],
        tradeoff="Frequent upstream breaking changes; heavy dependency tree if pulling full langchain package.",
        alternative="LlamaIndex / Raw custom parsing scripts",
        when_to_change="If package size becomes a constraint in serverless Lambda functions; would extract standalone regex chunkers."
    ))

    # Decision Card 4: Google Gemini Embedding 2
    html_out.append(b.build_decision_card(
        title="Why Google Gemini Embedding 2?",
        decision="Google GenAI gemini-embedding-2 with 768 output dimensions.",
        rationale_list=[
            "High semantic density across technical prose, tabular records, and multi-language documentation.",
            "Supports asymmetric retrieval tasks (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY).",
            "768 dimensions require 50% less RAM and disk than 1536-dim OpenAI models while offering higher recall."
        ],
        tradeoff="External network dependency subject to Google API quotas and WAN latency (~200ms per batch).",
        alternative="OpenAI text-embedding-3-small / Local BGE-large-en",
        when_to_change="If documents contain classified defense or air-gapped data requiring 100% on-premises local embeddings (e.g. HuggingFace TEI)."
    ))

    # Decision Card 5: ChromaDB
    html_out.append(b.build_decision_card(
        title="Why ChromaDB?",
        decision="Embedded ChromaDB PersistentClient with SQLite metadata and HNSW vector index.",
        rationale_list=[
            "Zero external database server to deploy, monitor, or manage in development.",
            "Instant local disk persistence under ./data/chroma_db.",
            "Native metadata filtering (where={'source': filename}) and Euclidean L2 distance."
        ],
        tradeoff="Embedded SQLite write locks limit FastAPI to single-process concurrency on write operations.",
        alternative="Qdrant / Pinecone / pgvector",
        when_to_change="At multi-pod horizontal scaling where multiple FastAPI containers must concurrently write to a shared vector database."
    ))

    # Decision Card 6: Redis Query Cache
    html_out.append(b.build_decision_card(
        title="Why Redis Query Cache?",
        decision="Standalone Redis container caching normalized query responses with 1-hour TTL.",
        rationale_list=[
            "Reduces query latency from ~1.8 seconds to sub-10 milliseconds for frequent questions.",
            "Slashes external LLM and embedding API expenses by up to 90%.",
            "Enables simple blanket or key-based cache invalidation upon document updates."
        ],
        tradeoff="Introduces an external infrastructure dependency requiring Docker container management.",
        alternative="In-memory Python dictionary (e.g. cachetools)",
        when_to_change="An in-memory dictionary fails when scaling horizontally across multiple FastAPI processes; Redis is the correct distributed choice."
    ))

    # Decision Card 7: OpenRouter AI Gateway
    html_out.append(b.build_decision_card(
        title="Why OpenRouter AI Gateway?",
        decision="OpenRouter gateway routing completions to google/gemini-2.5-flash.",
        rationale_list=[
            "Zero code changes required to switch between underlying foundation models (Anthropic, OpenAI, Google).",
            "Consolidated corporate billing, usage monitoring, and rate limit management.",
            "Standardized OpenAI-compatible wire protocol."
        ],
        tradeoff="Adds a proxy network hop (~30ms) between our backend and the foundation model provider.",
        alternative="Direct Google AI Studio API / Azure OpenAI",
        when_to_change="If enterprise compliance prohibits third-party API aggregators, we would switch to direct Azure OpenAI enterprise agreements."
    ))

    # Decision Card 8: Google Gemini 2.5 Flash
    html_out.append(b.build_decision_card(
        title="Why Google Gemini 2.5 Flash?",
        decision="google/gemini-2.5-flash with temperature 0.2 and max_tokens 4096.",
        rationale_list=[
            "State-of-the-art context window reasoning and strict adherence to negative constraints ('Answer ONLY from context').",
            "Blazing generation latency (~800ms) compared to heavier models (~2.5s).",
            "Ultra-low per-token pricing ideal for cost-efficient enterprise deployment."
        ],
        tradeoff="Slightly less capable than Claude 3.5 Sonnet on complex mathematical proofs or intricate code generation.",
        alternative="Claude 3.5 Sonnet / GPT-4o-mini",
        when_to_change="If the domain shifts from factual corporate QA to complex multi-step code synthesis requiring Claude Sonnet."
    ))

    # Decision Card 9: Client-Side localStorage
    html_out.append(b.build_decision_card(
        title="Why localStorage for Chat Persistence?",
        decision="Browser localStorage storing serialized message arrays under nexusrag:chat-history:v1.",
        rationale_list=[
            "Zero database tables, zero session cookies, and zero server storage required for chat history.",
            "Instant client-side restoration on page reloads and tab navigation.",
            "Completely client-isolated: users never see other users' conversation histories."
        ],
        tradeoff="Limited to ~5MB browser quota; conversations do not synchronize across devices or browsers.",
        alternative="Server-side PostgreSQL chat session table",
        when_to_change="When implementing multi-user authentication where users expect cross-device chat sync and server-side chat export."
    ))

    # Decision Card 10: Docker & Docker Compose
    html_out.append(b.build_decision_card(
        title="Why Docker & Docker Compose?",
        decision="Multi-container orchestration for FastAPI backend and Redis service.",
        rationale_list=[
            "Guarantees 100% environment parity across local development, CI/CD testing, and staging.",
            "Single-command bootstrap (docker-compose up) launches backend, dependencies, and network bridges.",
            "Enforces clear resource isolation and healthcheck monitoring."
        ],
        tradeoff="Requires Docker Desktop daemon on local developer machines.",
        alternative="Bare-metal virtualenv + locally installed Redis service",
        when_to_change="In production, Docker containers transition to Kubernetes (EKS) or AWS ECS Fargate task definitions."
    ))

    # Section 38: Comprehensive Trade-offs Matrix
    html_out.append(b.build_section_header(
        num_str="38",
        title="Comprehensive Trade-offs & Architectural Compromises Matrix",
        summary="Detailed evaluation of 8 core technical decisions, balancing immediate engineering benefits against architectural costs.",
        sec_id="sec-38"
    ))

    tradeoffs = [
        ("Embedded ChromaDB", "ChromaDB PersistentClient on local disk", "Zero external database setup; instant local persistence without container management.", "SQLite file locks prevent horizontal multi-pod concurrent writes.", "Single-server constraint; cannot scale FastAPI horizontally.", "Migrate to standalone Qdrant or Milvus cluster."),
        ("Vanilla CSS Design Tokens", "Pure CSS custom properties without Tailwind", "Zero build-step dependencies; ultra-fast dev server HMR; 100% style control.", "Manual maintenance of token conventions across a large CSS stylesheet.", "No compile-time unused class purging; stylesheet file size is larger.", "Adopt Tailwind CSS v4 or CSS modules."),
        ("localStorage Chat History", "Browser-side localStorage persistence", "Zero server database overhead; instant reads; zero user session management.", "Storage ceiling of ~5MB; plain text unencrypted in browser.", "Conversations do not sync across devices; clearing browser data wipes chats.", "PostgreSQL database with user authentication."),
        ("Dense-Only Vector Retrieval", "768-dim dense similarity search", "High semantic understanding of queries that do not share exact keywords.", "Susceptible to false positives on exact alphanumeric codes or acronyms.", "Occasional retrieval failures on exact part numbers or error codes.", "Hybrid BM25 keyword search + dense vector reciprocal rank fusion (RRF)."),
        ("Recursive Character Splitting", "800-char chunks with 100 overlap", "Maintains paragraph and sentence boundaries without mid-word cutting.", "Lacks structural awareness of complex tabular data spanning multiple rows.", "Tables split across chunk boundaries can lose column headers.", "Layout-aware chunking (Unstructured.io / Docling table parsers)."),
        ("Blanket Redis Invalidation", "redis_cache.clear() on any document change", "Guarantees absolute freshness; zero possibility of serving outdated answers.", "Clears all cached queries, even for unrelated documents.", "Temporary latency spike (cache stampede) as queries re-populate cache.", "Tag-based fine-grained cache invalidation mapping doc_id to query keys."),
        ("Filename as Document Identity", "Canonical filename acts as unique identifier", "Intuitive for users; matches desktop document management conventions.", "Uploading a file with the same name overwrites existing document vectors.", "Cannot maintain multiple revisions of the same filename simultaneously.", "Content-addressable SHA-256 hashing + database document registry."),
        ("OpenRouter Gateway", "API gateway proxy for LLM completions", "Unified billing, multi-model failover, standardized OpenAI protocol.", "Adds an external network proxy hop (~30ms latency).", "Third-party dependency; requires OpenRouter service uptime.", "Direct enterprise Azure OpenAI or AWS Bedrock private VPC peering.")
    ]

    for title, dec, ben, cost, lim, prod in tradeoffs:
        html_out.append(b.build_tradeoff_card(title, dec, ben, cost, lim, prod))

    # Section 39: Architectural Limitations
    html_out.append(b.build_section_header(
        num_str="39",
        title="Architectural Limitations & Honest Reality Check",
        summary="Clear engineering demarcation of current system boundaries and non-implemented capabilities.",
        sec_id="sec-39"
    ))

    html_out.append("""
    <div class="content-block">
      <div class="callout callout-limitation no-break">
        <div class="callout-header"><span>🚧</span> HONEST SYSTEM BOUNDARIES</div>
        <p>
          In an interview defense, acknowledging limitations demonstrates senior engineering maturity. NexusRAG has explicit, deliberate boundaries:
        </p>
        <ul>
          <li><strong>No User Authentication / RBAC:</strong> The system currently operates in open internal mode. All uploaded documents are visible to all users.</li>
          <li><strong>No Streaming LLM Responses:</strong> Responses are returned as atomic HTTP JSON payloads. Users wait ~1.5s for the complete response rather than seeing token streaming.</li>
          <li><strong>No Multi-Turn Conversation-Aware Retrieval:</strong> The retriever embeds only the current user query without rewriting it using conversational context from previous turns.</li>
          <li><strong>No OCR for Scanned Documents:</strong> Scanned PDF documents consisting purely of bitmap images yield zero extractable text and are rejected with HTTP 422.</li>
          <li><strong>Single Collection Architecture:</strong> All documents reside in collection <code>nexusrag_documents</code> without multi-tenant departmental isolation.</li>
        </ul>
      </div>
    </div>
    """)

    # Section 40: Advanced RAG Evolution
    html_out.append(b.build_section_header(
        num_str="40",
        title="Advanced RAG Evolution Roadmap (V1 to V7)",
        summary="Strategic phased enhancement roadmap from Dense Vector Baseline to Graph RAG.",
        sec_id="sec-40"
    ))

    html_out.append("""
    <div class="content-block">
      <table>
        <thead>
          <tr>
            <th>Version</th>
            <th>RAG Capability</th>
            <th>Primary Engineering Enhancement</th>
            <th>Implementation Status</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>V1</strong></td>
            <td>Dense Vector RAG</td>
            <td>Gemini Embedding 2 + ChromaDB Top-4 + OpenRouter Gemini 2.5 + Redis Cache.</td>
            <td><span class="status-badge implemented">CURRENT ARCHITECTURE</span></td>
          </tr>
          <tr>
            <td><strong>V2</strong></td>
            <td>Hybrid Search</td>
            <td>BM25 sparse keyword index combined with dense vectors via Reciprocal Rank Fusion (RRF).</td>
            <td><span class="status-badge future">PLANNED PHASE 16</span></td>
          </tr>
          <tr>
            <td><strong>V3</strong></td>
            <td>Cross-Encoder Reranking</td>
            <td>Cohere Rerank or BGE-Reranker-large rescoring Top-20 retrieved chunks down to Top-4.</td>
            <td><span class="status-badge future">PLANNED PHASE 17</span></td>
          </tr>
          <tr>
            <td><strong>V4</strong></td>
            <td>Automated RAGAS Evaluation</td>
            <td>Automated CI/CD quality testing measuring Faithfulness, Relevance, and Precision.</td>
            <td><span class="status-badge future">PLANNED PHASE 18</span></td>
          </tr>
          <tr>
            <td><strong>V5</strong></td>
            <td>Query Rewriting &amp; Multi-Query</td>
            <td>Sub-agent rewriting conversational follow-ups into standalone search queries.</td>
            <td><span class="status-badge future">PLANNED PHASE 19</span></td>
          </tr>
          <tr>
            <td><strong>V6</strong></td>
            <td>Production Cloud Scaling</td>
            <td>AWS ECS Fargate, Qdrant cluster, ElastiCache Redis, S3 document storage.</td>
            <td><span class="status-badge production">PRODUCTION ROADMAP</span></td>
          </tr>
          <tr>
            <td><strong>V7</strong></td>
            <td>Graph RAG (Knowledge Graph)</td>
            <td>Neo4j entity-relation extraction for multi-hop structural reasoning across documents.</td>
            <td><span class="status-badge future">LONG-TERM ROADMAP</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    """)

    # Section 41: RAGAS Evaluation Framework
    html_out.append(b.build_section_header(
        num_str="41",
        title="RAG Evaluation Framework & Metric Definitions (RAGAS)",
        summary="Automated quality assessment metrics evaluating retrieval precision, grounding faithfulness, and answer relevance.",
        sec_id="sec-41"
    ))

    html_out.append("""
    <div class="content-block">
      <p>
        To evaluate RAG quality systematically without relying on subjective human inspection, NexusRAG specifies the <strong>RAGAS (Retrieval Augmented Generation Assessment)</strong> evaluation triad:
      </p>
      <table>
        <thead>
          <tr>
            <th>Evaluation Metric</th>
            <th>Mathematical Focus</th>
            <th>Formula / Conceptual Ratio</th>
            <th>What It Catches</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Faithfulness</strong></td>
            <td>Generation Quality</td>
            <td><code>|Supported Claims| / |Total Claims|</code></td>
            <td>Hallucinations where the LLM asserts facts not present in retrieved context.</td>
          </tr>
          <tr>
            <td><strong>Answer Relevance</strong></td>
            <td>Generation Quality</td>
            <td>Cosine similarity of question embedding vs reverse-engineered questions.</td>
            <td>Answers that are factually grounded but wander off-topic and fail to answer the user's question.</td>
          </tr>
          <tr>
            <td><strong>Context Precision</strong></td>
            <td>Retrieval Quality</td>
            <td>Mean Average Precision (MAP) of relevant chunks in Top-K.</td>
            <td>Retriever noise where relevant chunks are ranked below irrelevant chunks.</td>
          </tr>
          <tr>
            <td><strong>Context Recall</strong></td>
            <td>Retrieval Quality</td>
            <td><code>|Retrieved Ground Truth Entities| / |Total Ground Truth Entities|</code></td>
            <td>Retriever misses where critical paragraphs necessary to answer are omitted from Top-K.</td>
          </tr>
        </tbody>
      </table>
    </div>
    """)

    return "".join(html_out)

print("Part VII generator ready.")
