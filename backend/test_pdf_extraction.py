
import json
import time
from pathlib import Path

from services.document_processing.pipeline import (
    create_default_document_processing_pipeline,
)


BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "test_pdfs"
OUTPUT_DIR = BASE_DIR / "test_output"

OUTPUT_DIR.mkdir(exist_ok=True)

document_processing_pipeline = (
    create_default_document_processing_pipeline()
)

def test_pdf(pdf_path: Path):
    print(f"\nProcessing: {pdf_path.name}")

    start_time = time.perf_counter()

    try:
        result = document_processing_pipeline.process(str(pdf_path))
        elapsed_time = time.perf_counter() - start_time

        pages = result.get("pages", [])
        total_blocks = sum(
            len(page.get("blocks", []))
            for page in pages
        )

        extracted_text = "\n\n".join(
            f"--- PAGE {page['page']} ---\n{page['text']}"
            for page in pages
        )

        output = {
            "filename": pdf_path.name,
            "metadata": result.get("metadata", {}),
            "page_count": len(pages),
            "total_blocks": total_blocks,
            "processing_time_seconds": round(elapsed_time, 3),
            "pages": pages,
        }

        json_path = OUTPUT_DIR / f"{pdf_path.stem}.json"
        text_path = OUTPUT_DIR / f"{pdf_path.stem}.txt"

        json_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        text_path.write_text(
            extracted_text,
            encoding="utf-8",
        )

        print(f"Pages: {len(pages)}")
        print(f"Blocks: {total_blocks}")
        print(f"Processing time: {elapsed_time:.3f}s")
        print(f"Saved: {json_path.name}")

        return {
            "filename": pdf_path.name,
            "status": "success",
            "pages": len(pages),
            "blocks": total_blocks,
            "processing_time": round(elapsed_time, 3),
        }

    except Exception as error:
        print(f"FAILED: {error}")

        return {
            "filename": pdf_path.name,
            "status": "failed",
            "error": str(error),
        }


def main():
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDFs found in: {PDF_DIR}")
        return

    print(f"Found {len(pdf_files)} PDF(s)")

    results = []

    for pdf_path in pdf_files:
        results.append(test_pdf(pdf_path))

    report_path = OUTPUT_DIR / "summary.json"

    report_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print("\n========== SUMMARY ==========")

    for result in results:
        print(result)

    print(f"\nSummary saved to: {report_path}")


if __name__ == "__main__":
    main()
