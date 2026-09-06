from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.ingestion.loader import (
    CorruptedFileError,
    DocumentLoaderFactory,
    EmptyContentError,
    EmptyFileError,
    FileNotFoundIngestionError,
    FileTooLargeError,
    IngestionError,
    UnsupportedFileTypeError,
)

logger = get_logger(__name__)


class DocumentService:
    """Orchestrates document validation, parsing, metadata extraction, and ingestion."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initializes the DocumentService with configuration settings.

        Args:
            settings: Application Settings instance. Defaults to get_settings().
        """
        self.settings = settings or get_settings()

    def validate_file(self, file_path: Path) -> None:
        """Performs rigorous pre-flight validation on the input file path.

        Args:
            file_path: Target filesystem Path.

        Raises:
            FileNotFoundIngestionError: If the path does not exist or is not a file.
            UnsupportedFileTypeError: If the file extension is not permitted.
            EmptyFileError: If the file size is zero bytes.
            FileTooLargeError: If the file exceeds the configured max size limit.
        """
        if not file_path.exists():
            raise FileNotFoundIngestionError(
                f"Document '{file_path.name}' does not exist at '{file_path}'."
            )

        if not file_path.is_file():
            raise FileNotFoundIngestionError(
                f"Path '{file_path}' is a directory, not a valid document file."
            )

        # Validate file extension
        suffix = file_path.suffix.lower()
        if suffix not in self.settings.allowed_extensions:
            allowed = ", ".join(self.settings.allowed_extensions)
            raise UnsupportedFileTypeError(
                f"File extension '{suffix}' for '{file_path.name}' is not supported. "
                f"Allowed formats: {allowed}"
            )

        # Validate file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise EmptyFileError(f"Document '{file_path.name}' is empty (0 bytes).")

        max_size = self.settings.max_file_size_bytes
        if file_size > max_size:
            max_mb = self.settings.ingestion.max_file_size_mb
            size_mb = file_size / (1024 * 1024)
            raise FileTooLargeError(
                f"Document '{file_path.name}' size ({size_mb:.2f} MB) exceeds "
                f"configured limit of {max_mb} MB."
            )

    def ingest_file(
        self, file_path: str | Path, original_filename: Optional[str] = None
    ) -> List[Document]:
        """Ingests, validates, parses, and standardizes a single document.

        Args:
            file_path: Path string or Path object pointing to the document.
            original_filename: Optional original sanitized filename (e.g. before staging).
                When provided, overrides document source and file_name metadata.

        Returns:
            List of structured LangChain Document objects ready for chunking.

        Raises:
            IngestionError: If validation or loading fails.
        """
        path = Path(file_path).resolve()
        filename = path.name

        logger.info("Ingestion started for document: '%s'", filename)

        try:
            self.validate_file(path)
            loader = DocumentLoaderFactory.get_loader(path)
            logger.info("Detected file format '%s' for '%s'", path.suffix.lower(), filename)

            documents = loader.load(path)

            canonical_name = original_filename or filename
            for doc in documents:
                doc.metadata["source"] = canonical_name
                doc.metadata["file_name"] = canonical_name

            # Ensure extractable text exists across the document pages
            has_content = any(doc.page_content.strip() for doc in documents)
            if not has_content:
                logger.warning("No extractable text found in '%s'", filename)
                raise EmptyContentError(
                    f"Document '{filename}' contains no extractable textual content."
                )

            logger.info(
                "Ingestion completed for '%s': successfully extracted %d document/page item(s)",
                filename,
                len(documents),
            )
            return documents

        except IngestionError as e:
            logger.warning("Ingestion rejected for '%s': %s", filename, e)
            raise
        except Exception as e:
            logger.error("Unexpected failure during ingestion of '%s': %s", filename, e)
            raise IngestionError(
                f"Unexpected failure while ingesting '{filename}': {e}"
            ) from e

    def ingest_directory(
        self, directory_path: str | Path, recursive: bool = False
    ) -> List[Document]:
        """Batch-ingests all supported documents located within a directory.

        Args:
            directory_path: Directory containing target documents.
            recursive: Whether to scan subdirectories recursively.

        Returns:
            Aggregated list of all extracted LangChain Document objects.
        """
        dir_path = Path(directory_path).resolve()
        if not dir_path.is_dir():
            raise FileNotFoundIngestionError(f"Directory '{dir_path}' does not exist.")

        all_docs: List[Document] = []
        pattern = "**/*" if recursive else "*"

        logger.info("Scanning directory '%s' for ingestible documents", dir_path)

        for item in dir_path.glob(pattern):
            if item.is_file() and item.suffix.lower() in self.settings.allowed_extensions:
                try:
                    docs = self.ingest_file(item)
                    all_docs.extend(docs)
                except IngestionError as e:
                    logger.warning("Skipping file '%s' due to ingestion error: %s", item.name, e)

        logger.info(
            "Directory scan finished for '%s': %d total document items ingested",
            dir_path,
            len(all_docs),
        )
        return all_docs
