from pathlib import Path
from typing import Any

import pymupdf

from services.document_processing.base import PDFProcessor


class PyMuPDFProcessor(PDFProcessor):
    """
    Reads a text-based PDF and returns its raw layout information.

    This class extracts facts from the PDF. It does not decide whether
    text is a heading, list item, or paragraph. That work will happen
    later in normalizer.py.
    """

    def extract(self, file_path: str) -> dict[str, Any]:
        pdf_path = Path(file_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file was not found: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported")

        try:
            document = pymupdf.open(pdf_path)
        except Exception as exc:
            raise ValueError("The uploaded file is not a valid PDF") from exc

        try:
            pages = []

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
                "page_count": len(document),
                "pages": pages,
            }

        finally:
            document.close()