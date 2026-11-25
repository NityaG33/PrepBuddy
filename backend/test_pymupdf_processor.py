
import json
import sys

from services.document_processing.pymupdf_processor import PyMuPDFProcessor


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python test_pymupdf_processor.py path/to/file.pdf"
        )

    processor = PyMuPDFProcessor()
    result = processor.extract(sys.argv[1])

    print(f"Pages: {result['page_count']}")
    print(f"Metadata: {result['metadata']}")

    for page in result["pages"]:
        print(
            f"Page {page['page_number']}: "
            f"{len(page['blocks'])} text blocks"
        )

    print(json.dumps(result, indent=2, default=str)[:3000])


if __name__ == "__main__":
    main()
