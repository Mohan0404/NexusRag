"""Phase 13 — Deterministic End-to-End & Boundary Integration Tests.

Verifies:
1. IngestionPipeline strict orchestration ordering and failure containment.
2. ChromaStore + VectorRetriever integration with deterministic FakeEmbeddingService.
3. RAGPipeline + RedisQueryCache integration verifying behavioral cache hits.
4. Full system E2E workflow via FastAPI TestClient:
   Upload document -> Index -> Query chat -> Retrieve chunk -> Grounded LLM response ->
   Source citation -> Repeated equivalent query -> Verified cache hit (skips retriever & LLM).
"""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_ingestion_pipeline, get_rag_pipeline
from app.cache.redis_cache import RedisQueryCache
from app.chunking.chunker import DocumentChunker
from app.embeddings.embedder import BaseEmbeddingService, EmbeddingProviderError
from app.ingestion.document_service import DocumentService
from app.ingestion.pipeline import IngestionPipeline, IngestionResult
from app.main import app
from app.rag.pipeline import RAGPipeline
from app.retrieval.retriever import Retriever
from app.vectordb.chroma_store import ChromaStore, VectorStoreError
from tests.conftest import FakeEmbeddingService, FakeLLMService, FakeRedisClient


# =====================================================================
# 1. IngestionPipeline Orchestration & Strict Ordering
# =====================================================================


def test_ingestion_pipeline_strict_ordering_success() -> None:
    """IngestionPipeline executes steps in strict order and triggers cache clear on success."""
    execution_order = []

    mock_doc_service = MagicMock(spec=DocumentService)

    def step1(p):
        execution_order.append("document_service")
        doc = MagicMock()
        doc.page_content = "content"
        doc.metadata = {"source": "test.txt"}
        return [doc]

    mock_doc_service.ingest_file.side_effect = step1

    mock_chunker = MagicMock(spec=DocumentChunker)

    def step2(docs):
        execution_order.append("chunker")
        return docs

    mock_chunker.chunk_documents.side_effect = step2

    mock_embedder = MagicMock(spec=BaseEmbeddingService)

    def step3(chunks):
        execution_order.append("embedder")
        chunk = MagicMock()
        chunk.content = "content"
        chunk.embedding = [0.1] * 768
        chunk.metadata = {"source": "test.txt"}
        return [chunk]

    mock_embedder.embed_documents.side_effect = step3

    mock_chroma = MagicMock(spec=ChromaStore)

    def step4(emb_chunks):
        execution_order.append("chroma_store")
        return len(emb_chunks)

    mock_chroma.add_embedded_chunks.side_effect = step4

    mock_cache = MagicMock(spec=RedisQueryCache)

    def step5():
        execution_order.append("cache_clear")

    mock_cache.clear.side_effect = step5

    pipeline = IngestionPipeline(
        document_service=mock_doc_service,
        chunker=mock_chunker,
        embedding_service=mock_embedder,
        chroma_store=mock_chroma,
        cache=mock_cache,
    )

    result = pipeline.index_file(Path("test.txt"))

    assert result.chunks_created == 1
    assert result.cache_cleared is True
    assert execution_order == [
        "document_service",
        "chunker",
        "embedder",
        "chroma_store",
        "cache_clear",
    ]


def test_ingestion_pipeline_embedding_failure_aborts_chroma_and_cache() -> None:
    """If embedding generation fails, ChromaStore is not called and cache is not cleared."""
    mock_doc_service = MagicMock(spec=DocumentService)
    mock_doc_service.ingest_file.return_value = [MagicMock()]

    mock_chunker = MagicMock(spec=DocumentChunker)
    mock_chunker.chunk_documents.return_value = [MagicMock()]

    mock_embedder = MagicMock(spec=BaseEmbeddingService)
    mock_embedder.embed_documents.side_effect = EmbeddingProviderError("Gemini API connection failure")

    mock_chroma = MagicMock(spec=ChromaStore)
    mock_cache = MagicMock(spec=RedisQueryCache)

    pipeline = IngestionPipeline(
        document_service=mock_doc_service,
        chunker=mock_chunker,
        embedding_service=mock_embedder,
        chroma_store=mock_chroma,
        cache=mock_cache,
    )

    with pytest.raises(EmbeddingProviderError):
        pipeline.index_file(Path("test.txt"))

    mock_chroma.add_embedded_chunks.assert_not_called()
    mock_cache.clear.assert_not_called()


def test_ingestion_pipeline_chroma_failure_aborts_cache_clear() -> None:
    """If vector storage in ChromaStore fails, cache is NOT cleared."""
    mock_doc_service = MagicMock(spec=DocumentService)
    mock_doc_service.ingest_file.return_value = [MagicMock()]

    mock_chunker = MagicMock(spec=DocumentChunker)
    mock_chunker.chunk_documents.return_value = [MagicMock()]

    mock_embedder = MagicMock(spec=BaseEmbeddingService)
    mock_embedder.embed_documents.return_value = [MagicMock()]

    mock_chroma = MagicMock(spec=ChromaStore)
    mock_chroma.add_embedded_chunks.side_effect = VectorStoreError("Chroma disk full")

    mock_cache = MagicMock(spec=RedisQueryCache)

    pipeline = IngestionPipeline(
        document_service=mock_doc_service,
        chunker=mock_chunker,
        embedding_service=mock_embedder,
        chroma_store=mock_chroma,
        cache=mock_cache,
    )

    with pytest.raises(VectorStoreError):
        pipeline.index_file(Path("test.txt"))

    mock_cache.clear.assert_not_called()


# =====================================================================
# 2. ChromaDB + VectorRetriever Integration
# =====================================================================


def test_chroma_retrieval_integration(tmp_path: Path) -> None:
    """Integration test: Real ChromaStore on tmp_path + deterministic FakeEmbeddingService + VectorRetriever."""
    chroma_dir = tmp_path / "integration_chroma"
    chroma_store = ChromaStore(
        persist_directory=str(chroma_dir),
        collection_name="integration_collection",
    )
    embedder = FakeEmbeddingService(dimension=768)

    # Ingest two distinct documents using deterministic concept anchors
    from langchain_core.documents import Document

    doc_nexus = Document(
        page_content="NexusRAG is built by Genworx for enterprise AI knowledge assistance.",
        metadata={"source": "nexus_guide.txt", "file_type": "txt", "page": 1},
    )
    doc_hr = Document(
        page_content="Annual leave policy entitles full time staff to twenty vacation days.",
        metadata={"source": "hr_policy.txt", "file_type": "txt", "page": 2},
    )

    embedded_chunks = embedder.embed_documents([doc_nexus, doc_hr])
    chroma_store.add_embedded_chunks(embedded_chunks)

    retriever = Retriever(
        chroma_store=chroma_store,
        embedding_service=embedder,
    )

    # Query for NexusRAG
    results = retriever.retrieve("What is NexusRAG and who built it?", top_k=2)

    assert len(results) >= 1
    top_result = results[0]
    # The top retrieved chunk must be the NexusRAG document
    assert "Genworx" in top_result.content
    assert top_result.metadata["source"] == "nexus_guide.txt"
    assert top_result.metadata["page"] == 1


# =====================================================================
# 3. RAGPipeline + RedisQueryCache Behavioral Integration
# =====================================================================


def test_rag_pipeline_redis_cache_behavioral_hit(tmp_path: Path) -> None:
    """Integration test: First query invokes retriever+LLM; second equivalent query hits cache."""
    chroma_dir = tmp_path / "rag_cache_chroma"
    chroma_store = ChromaStore(
        persist_directory=str(chroma_dir),
        collection_name="rag_cache_collection",
    )
    embedder = FakeEmbeddingService(dimension=768)

    from langchain_core.documents import Document

    doc = Document(
        page_content="NexusRAG provides verifiable citations and grounded answers.",
        metadata={"source": "whitepaper.pdf", "file_type": "pdf", "page": 3},
    )
    chroma_store.add_embedded_chunks(embedder.embed_documents([doc]))

    retriever = Retriever(
        chroma_store=chroma_store,
        embedding_service=embedder,
    )

    fake_llm = FakeLLMService(canned_response="NexusRAG generates grounded answers with citations.")
    fake_redis = FakeRedisClient()
    query_cache = RedisQueryCache(redis_client=fake_redis, default_ttl=3600)

    rag = RAGPipeline(
        retriever=retriever,
        llm_service=fake_llm,
        cache=query_cache,
    )

    # 1. First query (Cache MISS)
    res1 = rag.query("What does NexusRAG provide?")
    assert res1.answer == "NexusRAG generates grounded answers with citations."
    assert len(res1.sources) == 1
    assert res1.sources[0].source == "whitepaper.pdf"
    assert len(fake_llm.calls) == 1
    assert fake_redis.setex_calls == 1

    # 2. Second equivalent query with casing and whitespace variance (Cache HIT)
    res2 = rag.query("   what does nexusrag provide?   ")
    assert res2.answer == "NexusRAG generates grounded answers with citations."
    assert len(res2.sources) == 1
    assert res2.sources[0].source == "whitepaper.pdf"

    # Behavioral assertion: LLM must NOT be called again
    assert len(fake_llm.calls) == 1, "LLM must not be called again on cache hit"


# =====================================================================
# 4. Deterministic End-to-End System Test (Full HTTP Workflow)
# =====================================================================


def test_full_system_e2e_workflow(tmp_path: Path) -> None:
    """Full E2E workflow: Upload document -> Index -> Query chat -> Verify answer & sources -> Verify cache hit."""
    # 1. Isolated dependencies
    chroma_dir = tmp_path / "e2e_chroma"
    chroma_store = ChromaStore(
        persist_directory=str(chroma_dir),
        collection_name="e2e_collection",
    )
    embedder = FakeEmbeddingService(dimension=768)
    fake_llm = FakeLLMService(canned_response="NexusRAG is built by Genworx for enterprise AI.")
    fake_redis = FakeRedisClient()
    query_cache = RedisQueryCache(redis_client=fake_redis, default_ttl=3600)

    doc_service = DocumentService()
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)

    ingestion_pipeline = IngestionPipeline(
        document_service=doc_service,
        chunker=chunker,
        embedding_service=embedder,
        chroma_store=chroma_store,
        cache=query_cache,
    )

    retriever = Retriever(
        chroma_store=chroma_store,
        embedding_service=embedder,
    )

    rag_pipeline = RAGPipeline(
        retriever=retriever,
        llm_service=fake_llm,
        cache=query_cache,
    )

    # 2. Configure FastAPI dependency overrides
    app.dependency_overrides[get_ingestion_pipeline] = lambda: ingestion_pipeline
    app.dependency_overrides[get_rag_pipeline] = lambda: rag_pipeline

    with TestClient(app) as client:
        # Step 1: Upload nexus_guide.txt
        file_content = b"NexusRAG is built by Genworx for enterprise AI."
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("nexus_guide.txt", file_content, "text/plain")},
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["status"] == "success"
        assert upload_data["filename"] == "nexus_guide.txt"
        assert upload_data["chunks_created"] >= 1

        # Step 2: Query chat via POST /api/v1/chat
        chat_response_1 = client.post(
            "/api/v1/chat",
            json={"question": "What is NexusRAG and who built it?"},
        )

        assert chat_response_1.status_code == 200
        chat_data_1 = chat_response_1.json()
        assert "Genworx" in chat_data_1["answer"]
        assert len(chat_data_1["sources"]) >= 1
        assert "nexus_guide.txt" in chat_data_1["sources"][0]["source"]
        assert len(fake_llm.calls) == 1

        # Step 3: Repeat equivalent question with varying casing/whitespace
        chat_response_2 = client.post(
            "/api/v1/chat",
            json={"question": "what is nexusrag and who built it?"},
        )

        assert chat_response_2.status_code == 200
        chat_data_2 = chat_response_2.json()
        assert "Genworx" in chat_data_2["answer"]
        assert chat_data_2["sources"] == chat_data_1["sources"]

        # Behavioral assertion: LLM call count remains 1 proving cache hit through API
        assert len(fake_llm.calls) == 1, "Cache hit must skip LLM invocation"

    app.dependency_overrides.clear()
