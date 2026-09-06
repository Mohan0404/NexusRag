# Phase 9 — RAG Pipeline

## 1. Objective

Implement the RAG pipeline orchestrator that wires together the
Phase 7 Retriever, Phase 9 prompt construction, and Phase 8 LLM
service into a single `query(question)` interface.

This is the core intelligence layer of the application — it takes
a user question, finds relevant knowledge, and generates a grounded
answer with source citations.

---

## 2. Files Created/Modified

| Action | File | Responsibility |
|--------|------|----------------|
| **IMPLEMENTED** | `app/prompts/templates.py` | RAG system prompt, context formatter, `build_rag_prompt()` |
| **IMPLEMENTED** | `app/prompts/__init__.py` | Public exports for the prompts module |
| **IMPLEMENTED** | `app/rag/pipeline.py` | `RAGPipeline` orchestrator, `RAGResponse`, `SourceReference`, `RAGPipelineError` |
| **IMPLEMENTED** | `app/rag/__init__.py` | Public exports for the RAG module |
| **CREATED** | `tests/test_rag.py` | 15 tests — mocked Retriever + FakeLLMService, zero real API calls |
| **CREATED** | `docs/phases/phase-09-rag-pipeline.md` | This file |

**No Phase 3–8 files were modified.**

---

## 3. Architecture

### Responsibility Separation

```
app/retrieval/retriever.py     → Document retrieval (Phase 7)
app/prompts/templates.py       → Prompt construction (Phase 9)
app/rag/pipeline.py            → Pipeline orchestration (Phase 9)
app/llm/llm_service.py         → LLM generation (Phase 8)
```

### Data Flow

```
User Question (str)
    ↓
┌──────────────────────────────────┐
│  RAGPipeline.query(question)     │  ← Orchestrator
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│  Retriever.retrieve(question)    │  ← Phase 7 (unchanged)
│  Input: question (unchanged)     │
│  Output: List[RetrievedChunk]    │
└──────────────────────────────────┘
    ↓
    ├── Empty list → Return NO_CONTEXT_ANSWER (LLM NOT called)
    │
    ├── Non-empty ↓
    ↓
┌──────────────────────────────────┐
│  build_rag_prompt(question,      │  ← app/prompts/templates.py
│                   chunks)        │
│  Output: formatted prompt string │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│  BaseLLMService.generate(prompt) │  ← Phase 8 (unchanged)
│  Output: LLMResponse             │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│  Response Assembly               │
│  - answer from LLMResponse       │
│  - sources from chunk metadata   │
│  Output: RAGResponse             │
└──────────────────────────────────┘
```

---

## 4. Prompt Structure

The prompt is constructed by `app/prompts/templates.py` and has three sections:

```
<System Instructions>
  - "Answer using ONLY the context provided"
  - "Do not guess or fabricate"
  - "Reference source and page when citing"

--- CONTEXT ---

[Source 1: hr_policy.pdf, Page 3]
Employees are entitled to 20 days of paid time off...

---

[Source 2: hr_policy.pdf, Page 5]
Remote work is allowed up to 3 days per week...

--- QUESTION ---

What is the leave policy?

--- ANSWER ---
```

### Why This Structure

1. **System instructions** ground the LLM — it must answer from context only.
2. **Numbered source headers** enable the LLM to cite specific sources.
3. **Clear section delimiters** (`--- CONTEXT ---`, `--- QUESTION ---`, `--- ANSWER ---`) help the model parse the prompt structure.
4. **The user's question appears verbatim** — it is never rewritten or transformed.

---

## 5. Empty Retrieval Behavior

When `Retriever.retrieve()` returns an empty list:

1. The LLM is **NOT called** — no generation occurs.
2. A controlled response is returned:

```python
NO_CONTEXT_ANSWER = (
    "I could not find any relevant information in the knowledge base "
    "to answer your question. Please try rephrasing your question or "
    "ensure that the relevant documents have been ingested."
)
```

3. `RAGResponse.sources` is empty.
4. `RAGResponse.model` is empty string.
5. `RAGResponse.context_chunks_used` is 0.

### Why

- Calling the LLM with no context would produce a hallucinated answer.
- A controlled response is honest and actionable — it tells the user what to do next.
- Skipping the LLM call saves cost and latency.

---

## 6. Source Citations

### SourceReference

```python
@dataclass
class SourceReference:
    source: str       # "hr_policy.pdf"
    file_type: str    # "pdf"
    page: int         # 3 (1-indexed)
```

### Deduplication Rule

Deduplication is at the **(source, page)** level:

| Chunks Retrieved | Sources Produced |
|-----------------|-----------------|
| `hr_policy.pdf` page 3 (chunk 0) | `hr_policy.pdf, page 3` |
| `hr_policy.pdf` page 3 (chunk 1) | *(deduplicated — same source+page)* |
| `hr_policy.pdf` page 5 (chunk 2) | `hr_policy.pdf, page 5` |
| `onboarding.md` page 1 (chunk 0) | `onboarding.md, page 1` |

**Total: 3 SourceReference entries**, not 4 (the duplicate page 3 is collapsed).

### Why Page-Level

- Different pages of the same document may contain different information.
- A citation like "hr_policy.pdf, Page 5" is more useful than just "hr_policy.pdf".
- For PDF documents, page numbers are essential for verification.

---

## 7. RAGResponse

```python
@dataclass
class RAGResponse:
    answer: str                          # Generated text or NO_CONTEXT_ANSWER
    sources: List[SourceReference]       # Deduplicated page-level citations
    query: str                           # Original user question (unchanged)
    model: str                           # LLM model name (empty if LLM not called)
    context_chunks_used: int             # Number of chunks in the prompt context
```

---

## 8. Error Handling

### Exception Hierarchy

```
RAGPipelineError  ← single orchestration boundary
    wraps:
    ├── RetrievalError (Phase 7)  — retrieval failures
    └── LLMError (Phase 8)        — generation failures
```

### Error Flow

| Failure Point | Original Exception | Wrapped As | LLM Called? |
|---------------|-------------------|------------|-------------|
| Empty query | — | `RAGPipelineError` directly | ❌ |
| Retriever fails | `RetrievalError` / `VectorSearchError` | `RAGPipelineError` | ❌ |
| LLM fails | `LLMError` / `LLMProviderError` | `RAGPipelineError` | ✅ (attempted) |
| No chunks found | — | *(not an error — controlled response)* | ❌ |

Exception chaining is always preserved: `RAGPipelineError.__cause__` references the original error.

### Why Minimal

- Only one new exception class: `RAGPipelineError`.
- No subclasses — the `__cause__` chain provides the specific error type.
- Callers (Phase 11 FastAPI endpoints) catch `RAGPipelineError` and inspect `__cause__` if needed.

---

## 9. Query Preservation

The user's original question string is passed **unchanged** through every step:

```
question = "What is the leave policy?"

Retriever.retrieve(question)           ← exact string
build_rag_prompt(question, chunks)     ← exact string
RAGResponse.query = question           ← exact string
```

The question is never:
- Lowercased
- Trimmed (beyond validation)
- Rewritten
- Expanded
- Augmented with keywords

---

## 10. Testing

### Test Suite: `tests/test_rag.py` — 15 tests

| # | Test | Verifies |
|---|------|---------|
| 1 | `test_retriever_receives_original_query` | Question passed unchanged to Retriever |
| 2 | `test_retrieved_chunks_appear_in_prompt` | All chunk texts appear in the LLM prompt |
| 3 | `test_original_query_appears_in_prompt` | User question appears verbatim in prompt |
| 4 | `test_llm_receives_constructed_prompt` | Prompt has CONTEXT/QUESTION/ANSWER structure |
| 5 | `test_llm_not_called_when_no_chunks` | Empty retrieval → LLM NOT called, controlled response |
| 6 | `test_sources_preserve_page_info` | Three chunks from 3 pages → 3 separate sources |
| 7 | `test_retrieval_error_handled` | VectorSearchError → RAGPipelineError |
| 8 | `test_llm_error_handled` | LLMProviderError → RAGPipelineError |
| 9 | `test_successful_rag_query` | Full pipeline → valid RAGResponse |
| 10 | `test_empty_query_rejected` | Empty/whitespace → RAGPipelineError |
| 11 | `test_llm_called_once` | LLM.generate() called exactly once |
| 12 | `test_source_deduplication_at_page_level` | Same (source, page) → one SourceReference |
| 13 | `test_response_includes_model_info` | RAGResponse.model from LLMResponse |
| 14 | `test_prompt_contains_grounding_instructions` | System prompt rules in the prompt |
| 15 | `test_retrieval_error_preserves_cause` | __cause__ chain preserved |

### Mocking Strategy

- `FakeLLMService`: Implements `BaseLLMService.generate()`, captures prompt, returns canned `LLMResponse`.
- `FailingLLMService`: Always raises `LLMProviderError`.
- `MagicMock(spec=Retriever)`: Returns canned `List[RetrievedChunk]`.
- **Zero real API calls** to Gemini, OpenRouter, or ChromaDB.

---

## 11. Design Decisions

### Why prompt logic is in `app/prompts/templates.py`

The prompt template is a separate concern from pipeline orchestration.
`pipeline.py` decides *when* to call the prompt builder and *what* to do
with the result. `templates.py` decides *how* to format the prompt.
This separation allows:
- Testing prompt formatting independently.
- Swapping prompt templates without modifying the pipeline.
- Clear responsibility boundaries.

### Why the LLM is not called on empty retrieval

A RAG application with no context should not generate answers.
Calling the LLM would produce a hallucinated response that:
- Is not grounded in any document.
- Cannot be verified against sources.
- Undermines trust in the system.

A controlled "no relevant info" message is honest, actionable, and free.

### Why `RAGResponse` lives in `app/rag/` not `app/models/`

`app/models/` is scaffolded for Phase 11 FastAPI request/response schemas
(Pydantic models with JSON serialization). `RAGResponse` is a business-logic
dataclass used internally by the pipeline. Phase 11 will create its own API
schemas that may reference `RAGResponse` fields.

### Why no streaming

Streaming adds complexity (SSE, partial responses, UI buffering) that
isn't needed until the React frontend (Phase 12). The synchronous
`generate()` API is sufficient for the current pipeline.

### Why no conversation memory

This is a single-turn RAG system. Each query is independent.
Conversation memory would require session management, which is
out of scope for V1.

---

## 12. Future Phase Connections

### Phase 10 — Redis Caching

Redis caching will wrap `RAGPipeline.query()`:
```
Cache Check → (miss) → RAGPipeline.query() → Cache Store → Response
             (hit)  → Cached Response
```
Phase 9's interface (`query(question) → RAGResponse`) is designed
to be easily wrapped by a caching layer.

### Phase 11 — FastAPI APIs

FastAPI endpoints will:
1. Accept a JSON request with `question`.
2. Call `RAGPipeline.query(question)`.
3. Serialize `RAGResponse` into a JSON response.

### Phase 12 — React Frontend

The React frontend will call the FastAPI endpoint and display:
- `RAGResponse.answer` as the main content.
- `RAGResponse.sources` as clickable citations.
- `RAGResponse.model` as a metadata footer.

---

## 13. Interview Knowledge

### What is RAG?

**Retrieval-Augmented Generation** (RAG) is a technique that combines
information retrieval with text generation. Instead of relying solely
on the LLM's training data, RAG first retrieves relevant documents
from a knowledge base, then provides those documents as context to
the LLM to generate a grounded answer.

### Why RAG Instead of Fine-Tuning?

| Aspect | RAG | Fine-Tuning |
|--------|-----|-------------|
| Knowledge updates | Instant (re-index documents) | Requires retraining |
| Cost | Low (retrieval + inference) | High (training compute) |
| Hallucination control | Grounded in retrieved context | No guarantee |
| Source attribution | Built-in (chunk metadata) | Not possible |
| Domain specificity | Any document collection | Requires curated dataset |
| Latency | Retrieval + generation | Generation only |

### RAG Pipeline Components

A production RAG system has four core components:

1. **Indexing Pipeline**: Ingest → Chunk → Embed → Store (Phases 3–6).
2. **Retrieval**: Query embedding → Similarity search → Top-K chunks (Phase 7).
3. **Augmentation**: Construct a grounded prompt with context + question (Phase 9).
4. **Generation**: LLM produces an answer conditioned on the context (Phase 8).

### Grounding

**Grounding** means constraining the LLM to answer based only on provided
context, rather than its parametric knowledge. The system prompt explicitly
states: "Answer using ONLY the context provided. Do not guess or fabricate."

Grounding reduces hallucination but doesn't eliminate it entirely. The LLM
may still misinterpret or over-extrapolate from the context.

### Context Window Management

The RAG prompt must fit within the LLM's context window. With Gemini 2.5 Flash
(1M tokens), this is rarely a concern for typical RAG applications. However,
best practice is to:
- Limit `top_k` to a reasonable number (4 by default).
- Use appropriately sized chunks (800 characters).
- Monitor total prompt length.

### Source Attribution

Source attribution is a key advantage of RAG over pure LLM generation.
By tracking metadata through the pipeline (source filename, page number),
the system can:
- Tell the user which documents support the answer.
- Enable verification by linking to specific pages.
- Build trust through transparency.

### Empty Retrieval Handling

When no relevant documents are found, the system has three options:
1. **Return nothing** — unhelpful, frustrating UX.
2. **Call the LLM anyway** — produces hallucinated, ungrounded answers.
3. **Return a controlled message** — honest, actionable, free. ← Our choice.

Option 3 is the correct choice for a grounded RAG system because it
maintains the contract that all answers are evidence-based.
