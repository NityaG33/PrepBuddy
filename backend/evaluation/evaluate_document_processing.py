import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time

from services.document_processing.pipeline import (
    create_default_document_processing_pipeline,
)


# Lets Windows print symbols such as bullets without encoding errors.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_report(
    pdf_path: Path,
    normalized_document: dict,
    processing_time_seconds: float,
) -> dict:
    """
    Turn normalized document data into a small evaluation report.

    This does not judge whether every heading is correct. It gives us
    measurable facts and examples that we can inspect manually.
    """
    blocks = normalized_document["blocks"]
    block_types = Counter(block["type"] for block in blocks)

    pages = []

    for page in normalized_document["pages"]:
        page_blocks = page["blocks"]

        pages.append(
            {
                "page": page["page"],
                "text_length": len(page["text"]),
                "block_count": len(page_blocks),
                "heading_count": sum(
                    block["type"] == "heading"
                    for block in page_blocks
                ),
                "paragraph_count": sum(
                    block["type"] == "paragraph"
                    for block in page_blocks
                ),
                "list_item_count": sum(
                    block["type"] == "list_item"
                    for block in page_blocks
                ),
            }
        )

    heading_examples = [
        {
            "page": block["page_number"],
            "level": block["heading_level"],
            "text": block["text"],
        }
        for block in blocks
        if block["type"] == "heading"
    ][:20]

    empty_pages = [
        page["page"]
        for page in normalized_document["pages"]
        if not page["text"].strip()
    ]

    return {
        "file": pdf_path.name,
        "processing_time_seconds": round(processing_time_seconds, 3),
        "page_count": normalized_document["page_count"],
        "body_font_size": normalized_document["body_font_size"],
        "total_normalized_blocks": len(blocks),
        "block_type_counts": dict(block_types),
        "empty_pages": empty_pages,
        "heading_examples": heading_examples,
        "pages": pages,
    }


def evaluate_pdf(
    pdf_path: Path,
    output_directory: Path,
) -> None:
    pipeline = create_default_document_processing_pipeline()

    start_time = time.perf_counter()

    try:
        normalized_document = pipeline.process(str(pdf_path))

        processing_time = time.perf_counter() - start_time

        report = build_report(
            pdf_path=pdf_path,
            normalized_document=normalized_document,
            processing_time_seconds=processing_time,
        )

        output_path = (
            output_directory
            / f"{pdf_path.stem}_processing_report.json"
        )

        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(
                report,
                output_file,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\nProcessed: {pdf_path.name}")
        print(f"Pages: {report['page_count']}")
        print(f"Time: {report['processing_time_seconds']} seconds")
        print(f"Blocks: {report['block_type_counts']}")
        print(f"Empty pages: {report['empty_pages']}")
        print(f"Report: {output_path}")

    except Exception as exc:
        processing_time = time.perf_counter() - start_time

        print(f"\nFailed: {pdf_path.name}")
        print(f"Reason: {exc}")
        print(f"Time before failure: {processing_time:.3f} seconds")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate PrepBuddy PDF extraction and normalization.",
    )

    parser.add_argument(
        "pdf_paths",
        nargs="*",
        type=Path,
        help="One or more PDF files to process.",
    )

    parser.add_argument(
        "--directory",
        type=Path,
        help="Process every PDF directly inside this directory.",
    )

    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("test_output/document_processing"),
        help="Directory where JSON reports will be saved.",
    )

    args = parser.parse_args()

    pdf_paths = list(args.pdf_paths)

    if args.directory:
        pdf_paths.extend(sorted(args.directory.glob("*.pdf")))

    if not pdf_paths:
        parser.error(
            "Provide PDF paths or use --directory with a folder of PDFs."
        )

    args.output_directory.mkdir(parents=True, exist_ok=True)

    for pdf_path in pdf_paths:
        evaluate_pdf(
            pdf_path=pdf_path,
            output_directory=args.output_directory,
        )


if __name__ == "__main__":
    main()