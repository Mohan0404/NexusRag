"""Document management router for NexusRAG (Phases 11 & 14).

Exposes:
- POST   /api/v1/documents/upload      - Upload and index a new document
- GET    /api/v1/documents             - List all indexed documents and statistics
- DELETE /api/v1/documents/{source}     - Delete a document and its chunks
- PUT    /api/v1/documents/{source}     - Replace/re-index an existing document
"""

from pathlib import Path
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import (
    get_chroma_store,
    get_ingestion_pipeline,
    get_query_cache,
    get_settings,
)
from app.cache.redis_cache import BaseQueryCache
from app.core.config import Settings
from app.core.logging import get_logger
from app.ingestion.loader import (
    CorruptedFileError,
    EmptyContentError,
    EmptyFileError,
    FileTooLargeError,
    IngestionError,
    UnsupportedFileTypeError,
)
from app.ingestion.pipeline import IngestionPipeline
from app.models.responses import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentSummary,
    DocumentUploadResponse,
)
from app.vectordb.chroma_store import ChromaStore, VectorStoreError

logger = get_logger(__name__)

router = APIRouter(tags=["Documents"])

CHUNK_READ_SIZE = 64 * 1024  # 64 KB streaming buffer


async def _stage_upload_file(
    file: UploadFile,
    settings: Settings,
) -> tuple[Path, str, str, int]:
    """Validates filename and extension, and streams upload content to disk.

    Returns:
        tuple: (staged_path, sanitized_filename, file_suffix, total_bytes)

    Raises:
        HTTPException: If validation fails or file is empty / oversized.
    """
    raw_filename = file.filename or ""
    sanitized_filename = Path(raw_filename).name.strip()

    if not sanitized_filename:
        logger.warning("Document upload rejected: empty or whitespace filename.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must not be empty or blank.",
        )

    file_suffix = Path(sanitized_filename).suffix.lower()
    if file_suffix not in settings.allowed_extensions:
        allowed = ", ".join(settings.allowed_extensions)
        logger.warning(
            "Document upload rejected: '%s' has unsupported extension '%s'. Allowed: %s",
            sanitized_filename,
            file_suffix,
            allowed,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{file_suffix}' is not supported. Allowed formats: {allowed}",
        )

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    staging_filename = f"{uuid.uuid4().hex}_{sanitized_filename}"
    staged_path = upload_dir / staging_filename

    total_bytes = 0
    max_bytes = settings.max_file_size_bytes

    try:
        with open(staged_path, "wb") as buffer:
            while chunk := await file.read(CHUNK_READ_SIZE):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    max_mb = settings.ingestion.max_file_size_mb
                    logger.warning(
                        "Document upload aborted: '%s' exceeds %d MB limit.",
                        sanitized_filename,
                        max_mb,
                    )
                    buffer.close()
                    if staged_path.exists():
                        staged_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds maximum allowed limit of {max_mb} MB.",
                    )
                buffer.write(chunk)

        if total_bytes == 0:
            if staged_path.exists():
                staged_path.unlink(missing_ok=True)
            logger.warning("Document upload rejected: '%s' is 0 bytes.", sanitized_filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        return staged_path, sanitized_filename, file_suffix, total_bytes
    except Exception:
        if staged_path.exists():
            try:
                staged_path.unlink(missing_ok=True)
            except Exception:
                pass
        raise


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and Index Document",
    description="Accepts a document (.pdf, .txt, .md), extracts content, splits into chunks, computes dense embeddings, indexes into ChromaDB, and invalidates the query cache.",
    responses={
        200: {"description": "Document successfully ingested and indexed."},
        400: {"description": "Invalid file type, missing filename, or empty file."},
        413: {"description": "File exceeds maximum size limit (10 MB)."},
        422: {"description": "Corrupted file or document with no extractable text."},
        500: {"description": "Internal ingestion, embedding, or vector database failure."},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload and index"),
    ingestion_pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
    settings: Settings = Depends(get_settings),
) -> DocumentUploadResponse:
    """Handles secure document upload and triggers the ingestion pipeline."""
    staged_path: Optional[Path] = None
    sanitized_filename = ""
    try:
        staged_path, sanitized_filename, file_suffix, total_bytes = await _stage_upload_file(file, settings)

        logger.info(
            "File '%s' safely staged as '%s' (%d bytes). Starting ingestion.",
            sanitized_filename,
            staged_path.name,
            total_bytes,
        )

        try:
            result = await run_in_threadpool(
                ingestion_pipeline.index_file, staged_path, sanitized_filename
            )
        except TypeError as err:
            if "positional argument" in str(err) or "original_filename" in str(err):
                result = await run_in_threadpool(ingestion_pipeline.index_file, staged_path)
            else:
                raise

        return DocumentUploadResponse(
            filename=sanitized_filename,
            file_type=file_suffix,
            file_size_bytes=total_bytes,
            chunks_created=result.chunks_created,
            status="success",
            message=f"Successfully ingested and indexed '{sanitized_filename}' ({result.chunks_created} chunks).",
        )

    except HTTPException:
        raise

    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except (EmptyFileError, EmptyContentError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            if isinstance(exc, EmptyContentError)
            else status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except CorruptedFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document '{sanitized_filename}' is corrupted and could not be parsed.",
        ) from exc

    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc

    except (IngestionError, VectorStoreError) as exc:
        logger.error(
            "Ingestion pipeline failed for '%s': %s", sanitized_filename, exc, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest and index document: {exc}",
        ) from exc

    except Exception as exc:
        logger.error(
            "Unexpected error during upload of '%s': %s",
            sanitized_filename,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the document.",
        ) from exc

    finally:
        await file.close()
        if staged_path and staged_path.exists():
            try:
                staged_path.unlink(missing_ok=True)
            except Exception as cleanup_err:
                logger.warning("Failed to remove staged file '%s': %s", staged_path, cleanup_err)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Indexed Documents",
    description="Returns all distinct documents indexed in ChromaDB along with chunk counts, file types, and timestamps.",
    responses={
        200: {"description": "List of indexed documents."},
        500: {"description": "ChromaDB retrieval failure."},
    },
)
async def list_documents(
    chroma_store: ChromaStore = Depends(get_chroma_store),
) -> DocumentListResponse:
    """Lists all documents currently indexed in the knowledge base."""
    try:
        raw_docs = await run_in_threadpool(chroma_store.list_sources)
        documents = [
            DocumentSummary(
                source=doc["source"],
                file_type=doc.get("file_type", ""),
                chunk_count=doc.get("chunk_count", 0),
                indexed_at=doc.get("indexed_at"),
            )
            for doc in raw_docs
        ]
        total_chunks = sum(doc.chunk_count for doc in documents)
        return DocumentListResponse(
            documents=documents,
            total_chunks=total_chunks,
        )
    except VectorStoreError as exc:
        logger.error("ChromaStore error while listing documents: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve indexed documents: {exc}",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error while listing documents: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving indexed documents.",
        ) from exc


@router.delete(
    "/documents/{source:path}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Indexed Document",
    description="Deletes all chunks associated with a source document from ChromaDB and invalidates the query cache.",
    responses={
        200: {"description": "Document successfully deleted."},
        404: {"description": "Document not found."},
        500: {"description": "Vector database or deletion failure."},
    },
)
async def delete_document(
    source: str,
    chroma_store: ChromaStore = Depends(get_chroma_store),
    cache: Optional[BaseQueryCache] = Depends(get_query_cache),
) -> DocumentDeleteResponse:
    """Deletes a document and its associated chunks from the knowledge base."""
    try:
        chunk_count = await run_in_threadpool(chroma_store.count_by_source, source)
        if chunk_count == 0:
            logger.warning("Delete document failed: '%s' not found.", source)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{source}' not found in the knowledge base.",
            )

        deleted_count = await run_in_threadpool(chroma_store.delete_by_source, source)
        actual_deleted = (
            deleted_count
            if (isinstance(deleted_count, int) and deleted_count > 0)
            else chunk_count
        )

        if cache is not None:
            try:
                await run_in_threadpool(cache.clear)
                logger.info("Redis query cache cleared after deleting document '%s'.", source)
            except Exception as exc:
                logger.warning("Failed to clear query cache after deleting document '%s': %s", source, exc)

        logger.info("Successfully deleted document '%s' (%d chunks removed).", source, actual_deleted)
        return DocumentDeleteResponse(
            source=source,
            chunks_deleted=actual_deleted,
            status="deleted",
        )
    except HTTPException:
        raise
    except VectorStoreError as exc:
        logger.error("ChromaStore error while deleting document '%s': %s", source, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {exc}",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error while deleting document '%s': %s", source, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the document.",
        ) from exc


@router.put(
    "/documents/{source:path}",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Replace and Re-index Document",
    description="Replaces an existing indexed document with a new uploaded file. Removes previous chunks and indexes new content.",
    responses={
        200: {"description": "Document successfully replaced and indexed."},
        400: {"description": "Invalid file type, missing filename, or empty file."},
        404: {"description": "Target document to replace not found."},
        413: {"description": "File exceeds maximum size limit (10 MB)."},
        422: {"description": "Corrupted file or document with no extractable text."},
        500: {"description": "Ingestion, embedding, or vector database failure."},
    },
)
async def replace_document(
    source: str,
    file: UploadFile = File(..., description="Replacement document file"),
    ingestion_pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
    chroma_store: ChromaStore = Depends(get_chroma_store),
    settings: Settings = Depends(get_settings),
) -> DocumentUploadResponse:
    """Replaces an existing document with a new file, re-indexing its contents."""
    # 1. Verify target source exists before proceeding
    chunk_count = await run_in_threadpool(chroma_store.count_by_source, source)
    if chunk_count == 0:
        logger.warning("Replace document failed: target '%s' not found.", source)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{source}' not found in the knowledge base.",
        )

    staged_path: Optional[Path] = None
    sanitized_filename = ""
    try:
        # 2. Stage and validate the new replacement file
        staged_path, sanitized_filename, file_suffix, total_bytes = await _stage_upload_file(file, settings)

        logger.info(
            "Replacing document '%s' with '%s' (%d bytes). Starting ingestion.",
            source,
            sanitized_filename,
            total_bytes,
        )

        # 3. Ingest and index the new replacement file FIRST
        # If indexing fails (e.g. embedding error, API limit), old vectors remain untouched!
        try:
            result = await run_in_threadpool(
                ingestion_pipeline.index_file, staged_path, sanitized_filename
            )
        except TypeError as err:
            if "positional argument" in str(err) or "original_filename" in str(err):
                result = await run_in_threadpool(ingestion_pipeline.index_file, staged_path)
            else:
                raise

        if not result or result.chunks_created <= 0:
            raise IngestionError(
                f"Replacement indexing produced no chunks for '{sanitized_filename}'."
            )

        # 4. Only delete old document vectors AFTER replacement indexing succeeds
        if source != sanitized_filename:
            await run_in_threadpool(chroma_store.delete_by_source, source)
        else:
            new_ids = getattr(result, "chunk_ids", None)
            await run_in_threadpool(chroma_store.delete_by_source, source, new_ids)

        return DocumentUploadResponse(
            filename=sanitized_filename,
            file_type=file_suffix,
            file_size_bytes=total_bytes,
            chunks_created=result.chunks_created,
            status="success",
            message=f"Successfully replaced '{source}' with '{sanitized_filename}' ({result.chunks_created} chunks).",
        )

    except HTTPException:
        raise

    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except (EmptyFileError, EmptyContentError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            if isinstance(exc, EmptyContentError)
            else status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except CorruptedFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document '{sanitized_filename}' is corrupted and could not be parsed.",
        ) from exc

    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc

    except (IngestionError, VectorStoreError) as exc:
        logger.error(
            "Ingestion pipeline failed during replacement for '%s': %s", sanitized_filename, exc, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest and index replacement document: {exc}",
        ) from exc

    except Exception as exc:
        logger.error(
            "Unexpected error during replacement of '%s': %s",
            source,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the replacement document.",
        ) from exc

    finally:
        await file.close()
        if staged_path and staged_path.exists():
            try:
                staged_path.unlink(missing_ok=True)
            except Exception as cleanup_err:
                logger.warning("Failed to remove staged file '%s': %s", staged_path, cleanup_err)
