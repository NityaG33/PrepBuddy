
import re
import statistics
import pymupdf


# Common heading patterns in educational documents
HEADING_PATTERNS = [
    re.compile(r"^(chapter|section|unit)\s+\d+", re.IGNORECASE),
    re.compile(r"^\d+(?:\.\d+)*\.?\s+\S+"),
    re.compile(r"^(introduction|conclusion|references|bibliography|appendix)$", re.IGNORECASE),
]


def is_bold_font(font_name: str, flags: int) -> bool:
    """
    Identify bold text using PDF font information.
    """
    bold_flag = bool(flags & 16)

    bold_name = any(
        keyword in font_name.lower()
        for keyword in ("bold", "semibold", "demi")
    )

    return bold_flag or bold_name


def detect_heading(block, body_font_size: float):
    """
    Classify a text block as a heading or paragraph.
    Returns its type, hierarchy level and confidence.
    """

    text = block["text"].strip()
    font_sizes = block["font_sizes"]

    if not text or not font_sizes:
        return "paragraph", None, 0.0

    average_font_size = statistics.mean(font_sizes)

    is_bold = block["is_bold"]
    is_numbered = any(
        pattern.search(text)
        for pattern in HEADING_PATTERNS
    )

    # Avoid classifying long paragraphs as headings
    if len(text) > 150:
        return "paragraph", None, 0.0

    confidence = 0.0

    # Font size relative to the typical body text
    if average_font_size >= body_font_size * 1.35:
        confidence += 0.55
    elif average_font_size >= body_font_size * 1.15:
        confidence += 0.35

    # Bold formatting is another heading signal
    if is_bold:
        confidence += 0.25

    # Numbered sections and chapter headings
    if is_numbered:
        confidence += 0.35

    # Headings are generally short and don't end like sentences
    if len(text) <= 100 and not text.endswith((".", "?", "!")):
        confidence += 0.10

    if confidence < 0.50:
        return "paragraph", None, confidence

    # Estimate heading hierarchy
    if average_font_size >= body_font_size * 1.5:
        level = 1
    elif average_font_size >= body_font_size * 1.2:
        level = 2
    else:
        level = 3

    # Numbered heading depth provides an additional signal
    number_match = re.match(r"^(\d+(?:\.\d+)*)", text)

    if number_match:
        number_depth = len(number_match.group(1).split("."))
        level = min(number_depth, 3)

    return "heading", level, min(confidence, 1.0)


def extract_text_from_pdf(file_path: str):
    pages = []

    with pymupdf.open(file_path) as document:

        metadata = document.metadata or {}

        for page_number, page in enumerate(document, start=1):

            page_data = page.get_text("dict", sort=True)

            text_blocks = []

            for block in page_data["blocks"]:

                if block.get("type") != 0:
                    continue

                lines = []
                block_font_sizes = []
                block_fonts = []
                bold_span_count = 0
                total_spans = 0

                for line in block["lines"]:
                    line_text = ""

                    for span in line["spans"]:
                        span_text = span["text"]
                        line_text += span_text

                        if span_text.strip():
                            block_font_sizes.append(span["size"])
                            block_fonts.append(span["font"])

                            total_spans += 1

                            if is_bold_font(
                                span["font"],
                                span.get("flags", 0),
                            ):
                                bold_span_count += 1

                    if line_text.strip():
                        lines.append(line_text)

                block_text = "\n".join(lines).strip()

                if not block_text:
                    continue

                text_blocks.append({
                    "text": block_text,
                    "bbox": block["bbox"],
                    "font_sizes": block_font_sizes,
                    "fonts": list(set(block_fonts)),
                    "is_bold": (
                        bold_span_count / total_spans >= 0.5
                        if total_spans else False
                    ),
                })

            # Estimate the typical body font size on this page
            all_font_sizes = [
                size
                for block in text_blocks
                for size in block["font_sizes"]
            ]

            body_font_size = (
                statistics.median(all_font_sizes)
                if all_font_sizes else 12.0
            )

            # Classify each extracted block
            for block in text_blocks:
                block_type, level, confidence = detect_heading(
                    block,
                    body_font_size,
                )

                block["type"] = block_type
                block["level"] = level
                block["heading_confidence"] = round(
                    confidence, 2
                )

            # Preserve the page-level text interface
            page_text = "\n\n".join(
                block["text"] for block in text_blocks
            )

            pages.append({
                "page": page_number,
                "text": page_text,
                "blocks": text_blocks,
                "body_font_size": body_font_size,
            })

    return {
        "metadata": metadata,
        "pages": pages,
    }
