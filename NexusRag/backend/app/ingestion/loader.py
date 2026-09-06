from abc import ABC, abstractmethod
from pathlib import Path
import re
from typing import Any, Dict, List
from langchain_core.documents import Document

from app.core.logging import get_logger

logger = get_logger(__name__)


# =====================================================================
# Ingestion Exceptions
# =====================================================================


class IngestionError(Exception):
    """Base exception for all document ingestion failures."""

    pass


class FileNotFoundIngestionError(IngestionError):
    """Raised when the target document does not exist on disk."""

    pass


class UnsupportedFileTypeError(IngestionError):
    """Raised when an uploaded document has an unsupported extension."""

    pass


class EmptyFileError(IngestionError):
    """Raised when the target document is 0 bytes."""

    pass


class FileTooLargeError(IngestionError):
    """Raised when a document exceeds the maximum allowable file size."""

    pass


class CorruptedFileError(IngestionError):
    """Raised when a document structure is corrupted or unreadable."""

    pass


class EmptyContentError(IngestionError):
    """Raised when a document contains no extractable textual content."""

    pass


# =====================================================================
# Document Loaders
# =====================================================================


class BaseDocumentLoader(ABC):
    """Abstract base class for format-specific document loaders."""

    @abstractmethod
    def load(self, file_path: Path) -> List[Document]:
        """Loads and extracts text and metadata from the target file.

        Args:
            file_path: Valid Path pointing to the document on disk.

        Returns:
            List of LangChain Document objects with standardized metadata.
        """
        pass

    @staticmethod
    def clean_text(text: str) -> str:
        """Sanitizes raw extracted text by removing null bytes and normalizing whitespace."""
        if not text:
            return ""
        # Remove null characters
        cleaned = text.replace("\x00", "")
        # Normalize carriage returns
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse multiple redundant blank lines (more than 2) to 2
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()


class PDFDocumentLoader(BaseDocumentLoader):
    """Document loader for PDF files utilizing PyPDF."""

    def load(self, file_path: Path) -> List[Document]:
        from langchain_community.document_loaders import PyPDFLoader

        try:
            loader = PyPDFLoader(str(file_path))
            raw_docs = loader.load()
        except Exception as e:
            logger.error("Failed to parse PDF '%s': %s", file_path.name, e)
            raise CorruptedFileError(
                f"PDF file '{file_path.name}' is corrupted or unreadable: {e}"
            ) from e

        if not raw_docs:
            raise EmptyContentError(
                f"PDF file '{file_path.name}' contains no readable pages."
            )

        file_size = file_path.stat().st_size
        total_pages = len(raw_docs)
        normalized_docs: List[Document] = []

        for idx, doc in enumerate(raw_docs):
            cleaned_content = self.clean_text(doc.page_content)
            # PyPDF provides 0-indexed 'page' in metadata; normalize to 1-indexed for citation
            raw_page = doc.metadata.get("page", idx)
            page_number = (raw_page + 1) if isinstance(raw_page, int) else (idx + 1)

            metadata: Dict[str, Any] = {
                "source": file_path.name,
                "file_name": file_path.name,
                "file_path": str(file_path.resolve()),
                "file_type": "pdf",
                "page": page_number,
                "total_pages": total_pages,
                "file_size_bytes": file_size,
            }

            # Retain non-conflicting optional loader metadata
            for key, val in doc.metadata.items():
                if key not in metadata and isinstance(val, (str, int, float, bool)):
                    metadata[key] = val

            normalized_docs.append(
                Document(page_content=cleaned_content, metadata=metadata)
            )

        return normalized_docs


class TextDocumentLoader(BaseDocumentLoader):
    """Document loader for plain text (.txt) files."""

    def load(self, file_path: Path) -> List[Document]:
        from langchain_community.document_loaders import TextLoader

        raw_docs = None
        # Attempt UTF-8 first, fallback to Latin-1
        for encoding in ("utf-8", "latin-1"):
            try:
                loader = TextLoader(str(file_path), encoding=encoding)
                raw_docs = loader.load()
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error("Error reading text file '%s': %s", file_path.name, e)
                raise CorruptedFileError(
                    f"Text file '{file_path.name}' cannot be read: {e}"
                ) from e

        if raw_docs is None:
            raise CorruptedFileError(
                f"Failed to decode text file '{file_path.name}' using supported encodings."
            )

        file_size = file_path.stat().st_size
        normalized_docs: List[Document] = []

        for doc in raw_docs:
            cleaned_content = self.clean_text(doc.page_content)
            metadata: Dict[str, Any] = {
                "source": file_path.name,
                "file_name": file_path.name,
                "file_path": str(file_path.resolve()),
                "file_type": "txt",
                "page": 1,
                "total_pages": 1,
                "file_size_bytes": file_size,
            }
            normalized_docs.append(
                Document(page_content=cleaned_content, metadata=metadata)
            )

        return normalized_docs


class MarkdownDocumentLoader(BaseDocumentLoader):
    """Document loader for Markdown (.md) files."""

    def load(self, file_path: Path) -> List[Document]:
        from langchain_community.document_loaders import TextLoader

        raw_docs = None
        for encoding in ("utf-8", "latin-1"):
            try:
                loader = TextLoader(str(file_path), encoding=encoding)
                raw_docs = loader.load()
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error("Error reading markdown file '%s': %s", file_path.name, e)
                raise CorruptedFileError(
                    f"Markdown file '{file_path.name}' cannot be read: {e}"
                ) from e

        if raw_docs is None:
            raise CorruptedFileError(
                f"Failed to decode markdown file '{file_path.name}' using supported encodings."
            )

        file_size = file_path.stat().st_size
        normalized_docs: List[Document] = []

        for doc in raw_docs:
            cleaned_content = self.clean_text(doc.page_content)
            metadata: Dict[str, Any] = {
                "source": file_path.name,
                "file_name": file_path.name,
                "file_path": str(file_path.resolve()),
                "file_type": "md",
                "page": 1,
                "total_pages": 1,
                "file_size_bytes": file_size,
            }
            normalized_docs.append(
                Document(page_content=cleaned_content, metadata=metadata)
            )

        return normalized_docs


# =====================================================================
# Loader Factory
# =====================================================================


class DocumentLoaderFactory:
    """Factory for selecting and instantiating appropriate document loaders based on file type."""

    _LOADERS = {
        ".pdf": PDFDocumentLoader,
        ".txt": TextDocumentLoader,
        ".md": MarkdownDocumentLoader,
    }

    @classmethod
    def get_loader(cls, file_path: Path) -> BaseDocumentLoader:
        """Resolves the loader corresponding to the file's extension.

        Args:
            file_path: Path to the document.

        Returns:
            Instance of BaseDocumentLoader.

        Raises:
            UnsupportedFileTypeError: If file extension is not supported.
        """
        suffix = file_path.suffix.lower()
        loader_cls = cls._LOADERS.get(suffix)
        if not loader_cls:
            supported = ", ".join(sorted(cls._LOADERS.keys()))
            raise UnsupportedFileTypeError(
                f"Unsupported file format '{suffix}'. Supported formats: {supported}"
            )
        return loader_cls()
