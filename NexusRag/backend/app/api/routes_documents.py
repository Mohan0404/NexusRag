"""Document upload endpoint router for NexusRAG (Phase 11).

Exposes POST /api/v1/documents/upload for ingesting, chunking, and indexing
knowledge base documents.
"""

from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import get_ingestion_pipeline, get_settings
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
from app.models.responses import DocumentUploadResponse
from app.vectordb.chroma_store import VectorStoreError

logger = get_logger(__name__)

router = APIRouter(tags=["Documents"])

CHUNK_READ_SIZE = 64 * 1024  # 64 KB streaming buffer


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
    # 1. Filename validation and sanitization
    raw_filename = file.filename or ""
    sanitized_filename = Path(raw_filename).name.strip()

    if not sanitized_filename:
        logger.warning("Document upload rejected: empty or whitespace filename.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must not be empty or blank.",
        )

    # 2. Extension validation against whitelist
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

    # 3. Secure staging directory setup
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    staging_filename = f"{uuid.uuid4().hex}_{sanitized_filename}"
    staged_path = upload_dir / staging_filename

    total_bytes = 0
    max_bytes = settings.max_file_size_bytes

    # 4. Stream file contents to disk while enforcing size bounds
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
                    # Close buffer before removing file
                    buffer.close()
                    if staged_path.exists():
                        staged_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds maximum allowed limit of {max_mb} MB.",
                    )
                buffer.write(chunk)

        # 5. Reject empty (0-byte) files
        if total_bytes == 0:
            if staged_path.exists():
                staged_path.unlink(missing_ok=True)
            logger.warning("Document upload rejected: '%s' is 0 bytes.", sanitized_filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        logger.info(
            "File '%s' safely staged as '%s' (%d bytes). Starting ingestion.",
            sanitized_filename,
            staging_filename,
            total_bytes,
        )

        # 6. Dispatch heavy ingestion pipeline to worker threadpool
        result = await run_in_threadpool(ingestion_pipeline.index_file, staged_path)

        return DocumentUploadResponse(
            filename=sanitized_filename,
            file_type=file_suffix,
            file_size_bytes=total_bytes,
            chunks_created=result.chunks_created,
            status="success",
            message=f"Successfully ingested and indexed '{sanitized_filename}' ({result.chunks_created} chunks).",
        )

    except HTTPException:
        # Re-raise explicit HTTP exceptions directly
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
