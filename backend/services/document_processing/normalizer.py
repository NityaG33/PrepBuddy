import re
import statistics
from typing import Any


HEADING_NUMBER_PATTERN = re.compile(
    r"^(?:chapter|section|unit)\s+\d+|^\d+(?:\.\d+)*\.?\s+\S+",
    re.IGNORECASE,
)

LIST_ITEM_PATTERN = re.compile(
    r"^(?:[•●▪◦\-–—*]|\(?\d+[.)]|\(?[a-zA-Z][.)])\s+"
)


def _clean_text(text: str) -> str:
    """Turn multiple spaces/newlines into one clean line of text."""
    return " ".join(text.split())


def _is_bold(font_name: str, flags: int) -> bool:
    font_name = font_name.lower()

    return (
        bool(flags & 16)
        or "bold" in font_name
        or "semibold" in font_name
        or "demi" in font_name
    )


class DocumentNormalizer:
    """
    Converts raw PDF extraction output into a consistent structure.

    Input:
        Raw pages, blocks, lines, and spans from PyMuPDFProcessor.

    Output:
        A document containing normalized headings, paragraphs, and lists.
    """

    def normalize(self, raw_document: dict[str, Any]) -> dict[str, Any]:
        body_font_size = self._find_body_font_size(raw_document)
        normalized_blocks = []

        for page in raw_document["pages"]:
            page_number = page["page_number"]

            for raw_block in page["blocks"]:
                block = self._normalize_block(
                    raw_block=raw_block,
                    page_number=page_number,
                    body_font_size=body_font_size,
                )

                if block is not None:
                    normalized_blocks.append(block)

        reconstructed_blocks = self._reconstruct_paragraphs(
            normalized_blocks,
            body_font_size,
        )

        pages = self._build_pages(
            raw_pages=raw_document["pages"],
            blocks=reconstructed_blocks,
        )

        return {
            "metadata": raw_document.get("metadata", {}),
            "page_count": raw_document.get("page_count", 0),
            "body_font_size": body_font_size,
            "blocks": reconstructed_blocks,
            "pages": pages,
        }

    def _find_body_font_size(self, raw_document: dict[str, Any]) -> float:
        """
        Estimate the normal text size in the document.

        The median is used because a PDF may contain a few large headings,
        but most text is usually normal paragraph text.
        """
        font_sizes = []

        for page in raw_document["pages"]:
            for block in page["blocks"]:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["text"].strip():
                            font_sizes.append(span["font_size"])

        return statistics.median(font_sizes) if font_sizes else 12.0

    def _normalize_block(
        self,
        raw_block: dict[str, Any],
        page_number: int,
        body_font_size: float,
    ) -> dict[str, Any] | None:
        lines = raw_block["lines"]

        line_texts = []
        font_sizes = []
        bold_spans = 0
        total_spans = 0

        for line in lines:
            line_text = "".join(span["text"] for span in line["spans"])
            line_text = _clean_text(line_text)

            if line_text:
                line_texts.append(line_text)

            for span in line["spans"]:
                if span["text"].strip():
                    font_sizes.append(span["font_size"])
                    total_spans += 1

                    if _is_bold(span["font"], span["flags"]):
                        bold_spans += 1

        text = _clean_text(" ".join(line_texts))

        if not text:
            return None

        average_font_size = (
            statistics.mean(font_sizes)
            if font_sizes
            else body_font_size
        )

        is_bold = (
            bold_spans / total_spans >= 0.5
            if total_spans
            else False
        )

        block_type, heading_level = self._classify_block(
            text=text,
            average_font_size=average_font_size,
            body_font_size=body_font_size,
            is_bold=is_bold,
        )

        return {
            "type": block_type,
            "text": text,
            "page_number": page_number,
            "bbox": raw_block["bbox"],
            "font_size": round(average_font_size, 2),
            "is_bold": is_bold,
            "heading_level": heading_level,
            "source_block_count": 1,
        }

    def _classify_block(
        self,
        text: str,
        average_font_size: float,
        body_font_size: float,
        is_bold: bool,
    ) -> tuple[str, int | None]:
        """
        Decide whether a block is a heading, list item, or paragraph.

        This is intentionally heuristic-based. We will improve its rules
        after examining results from your real educational PDFs.
        """
        is_short = len(text) <= 150
        is_numbered_heading = bool(HEADING_NUMBER_PATTERN.search(text))
        is_larger_than_body = average_font_size >= body_font_size * 1.15

        heading_score = 0

        if is_short and average_font_size >= body_font_size * 1.35:
            heading_score += 2

        if is_short and is_larger_than_body:
            heading_score += 1

        if is_short and is_bold:
            heading_score += 1

        if is_short and is_numbered_heading:
            heading_score += 2

        if heading_score >= 2:
            if average_font_size >= body_font_size * 1.5:
                level = 1
            elif average_font_size >= body_font_size * 1.2:
                level = 2
            else:
                level = 3

            return "heading", level

        if LIST_ITEM_PATTERN.match(text):
            return "list_item", None

        return "paragraph", None

    def _reconstruct_paragraphs(
        self,
        blocks: list[dict[str, Any]],
        body_font_size: float,
    ) -> list[dict[str, Any]]:
        """
        Merge nearby paragraph blocks when they are likely parts of
        one paragraph split by the PDF layout.
        """
        result = []

        for block in blocks:
            if not result:
                result.append(block)
                continue

            previous = result[-1]

            if self._should_merge(previous, block, body_font_size):
                previous["text"] = (
                    f"{previous['text']} {block['text']}"
                )
                previous["bbox"] = self._merge_bboxes(
                    previous["bbox"],
                    block["bbox"],
                )
                previous["source_block_count"] += 1
            else:
                result.append(block)

        return result

    def _build_pages(
        self,
        raw_pages: list[dict[str, Any]],
        blocks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Build a page-based compatibility view for the current chunker.

        The structured blocks remain the source of truth. The combined `text`
        field exists only because the Phase 2 application still uses the
        old fixed-character chunker.
        """
        blocks_by_page: dict[int, list[dict[str, Any]]] = {}

        for block in blocks:
            page_number = block["page_number"]
            blocks_by_page.setdefault(page_number, []).append(block)

        pages = []

        for raw_page in raw_pages:
            page_number = raw_page["page_number"]
            page_blocks = blocks_by_page.get(page_number, [])

            pages.append(
                {
                    # `page` is deliberately named to match chunking_service.py.
                    "page": page_number,

                    # The current chunker only understands text.
                    "text": "\n\n".join(
                        block["text"] for block in page_blocks
                    ),

                    # Phase 3 will use these structured blocks directly.
                    "blocks": page_blocks,
                }
            )

        return pages

    def _should_merge(
        self,
        previous: dict[str, Any],
        current: dict[str, Any],
        body_font_size: float,
    ) -> bool:
        if previous["type"] != "paragraph":
            return False

        if current["type"] != "paragraph":
            return False

        if previous["page_number"] != current["page_number"]:
            return False

        # If the old block clearly finishes a sentence, it is probably
        # already a complete paragraph.
        if previous["text"].endswith((".", "!", "?", ":", ";")):
            return False

        previous_bottom = previous["bbox"][3]
        current_top = current["bbox"][1]
        vertical_gap = current_top - previous_bottom

        # Nearby blocks with an unfinished previous line are likely
        # one paragraph split by PDF layout.
        return 0 <= vertical_gap <= body_font_size * 2

    def _merge_bboxes(
        self,
        first_bbox: tuple[float, float, float, float],
        second_bbox: tuple[float, float, float, float],
    ) -> tuple[float, float, float, float]:
        return (
            min(first_bbox[0], second_bbox[0]),
            min(first_bbox[1], second_bbox[1]),
            max(first_bbox[2], second_bbox[2]),
            max(first_bbox[3], second_bbox[3]),
        )