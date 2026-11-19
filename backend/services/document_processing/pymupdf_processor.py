from pathlib import Path
from typing import Any

import pymupdf

from core.config import MAX_EXTRACTED_TEXT_CHARS, MAX_PDF_PAGE_COUNT
from services.document_processing.base import PDFProcessor
from services.document_processing.errors import (
    DocumentProcessingValidationError,
)


class PyMuPDFProcessor(PDFProcessor):
    """
    Reads a text-based PDF and returns its raw layout information.

    This class extracts facts from the PDF. It does not decide whether
    text is a heading, list item, or paragraph. That work will happen
    later in normalizer.py.
    """

    def __init__(
        self,
        *,
        max_page_count: int = MAX_PDF_PAGE_COUNT,
        max_extracted_text_chars: int = MAX_EXTRACTED_TEXT_CHARS,
    ):
        self.max_page_count = max_page_count
        self.max_extracted_text_chars = max_extracted_text_chars

    def extract(self, file_path: str) -> dict[str, Any]:
        pdf_path = Path(file_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file was not found: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise DocumentProcessingValidationError(
                "Only PDF files are supported"
            )

        try:
            document = pymupdf.open(pdf_path)
        except Exception as exc:
            raise DocumentProcessingValidationError(
                "The uploaded file is not a valid PDF"
            ) from exc

        try:
            if document.needs_pass:
                raise DocumentProcessingValidationError(
                    "Password-protected PDFs are not supported"
                )

            page_count = len(document)

            if page_count > self.max_page_count:
                raise DocumentProcessingValidationError(
                    "PDF exceeds the configured page count limit"
                )

            pages = []
            extracted_text_chars = 0

            for page_number, page in enumerate(document, start=1):
                page_data = page.get_text("dict", sort=True)
                blocks = []

                for block in page_data.get("blocks", []):
                    # type 0 means a normal text block.
                    if block.get("type") != 0:
                        continue

                    lines = []

                    for line in block.get("lines", []):
                        spans = []

                        for span in line.get("spans", []):
                            text = span.get("text", "")

                            if not text:
                                continue

                            extracted_text_chars += len(text)

                            if (
                                extracted_text_chars
                                > self.max_extracted_text_chars
                            ):
                                raise DocumentProcessingValidationError(
                                    "PDF exceeds the configured extracted text limit"
                                )

                            spans.append(
                                {
                                    "text": text,
                                    "bbox": tuple(span["bbox"]),
                                    "font": span.get("font", ""),
                                    "font_size": span.get("size", 0.0),
                                    "flags": span.get("flags", 0),
                                }
                            )

                        if spans:
                            lines.append(
                                {
                                    "bbox": tuple(line["bbox"]),
                                    "spans": spans,
                                }
                            )

                    if lines:
                        blocks.append(
                            {
                                "bbox": tuple(block["bbox"]),
                                "lines": lines,
                            }
                        )

                pages.append(
                    {
                        "page_number": page_number,
                        "width": page.rect.width,
                        "height": page.rect.height,
                        "blocks": blocks,
                    }
                )

            return {
                "metadata": document.metadata or {},
                "page_count": page_count,
                "pages": pages,
            }

        finally:
            document.close()
