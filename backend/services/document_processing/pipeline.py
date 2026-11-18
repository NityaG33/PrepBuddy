from typing import Any

from services.document_processing.base import PDFProcessor
from services.document_processing.normalizer import DocumentNormalizer
from services.document_processing.pymupdf_processor import PyMuPDFProcessor


class DocumentProcessingPipeline:
    """
    Coordinates the document-processing steps.

    It does not know about FastAPI, databases, embeddings, or FAISS.
    Its only job is to turn a PDF file into a normalized document.
    """

    def __init__(
        self,
        processor: PDFProcessor,
        normalizer: DocumentNormalizer,
    ):
        self.processor = processor
        self.normalizer = normalizer

    def process(self, file_path: str) -> dict[str, Any]:
        """
        Extract raw PDF information, then normalize it into useful
        document structures such as pages, headings, and paragraphs.
        """
        raw_document = self.processor.extract(file_path)

        return self.normalizer.normalize(raw_document)


def create_default_document_processing_pipeline() -> DocumentProcessingPipeline:
    """
    Build the pipeline PrepBuddy currently uses.

    In the future, this is the one place where we can replace
    PyMuPDFProcessor with DoclingProcessor or an OCR processor.
    """
    return DocumentProcessingPipeline(
        processor=PyMuPDFProcessor(),
        normalizer=DocumentNormalizer(),
    )